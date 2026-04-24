"""Competitor public data collector — App Store & Google Play public info."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import httpx

from appagent_engine.net import retry_httpx_get
from appagent_engine.store.writer import atomic_write_json

# iTunes Lookup API (public, no auth)
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


def fetch_ios_app_info(app_id_or_bundle: str, country: str = "us") -> dict | None:
    """Fetch public app info from iTunes Lookup API.

    app_id_or_bundle: numeric App Store ID or bundle ID.
    """
    # Try as numeric ID first, then as bundle ID
    params = {"country": country}
    if app_id_or_bundle.isdigit():
        params["id"] = app_id_or_bundle
    else:
        params["bundleId"] = app_id_or_bundle

    resp = retry_httpx_get(ITUNES_LOOKUP_URL, timeout=15, params=params)

    results = resp.json().get("results", [])
    if not results:
        return None

    app = results[0]
    return {
        "name": app.get("trackName"),
        "bundle_id": app.get("bundleId"),
        "app_id": app.get("trackId"),
        "developer": app.get("artistName"),
        "price": app.get("price", 0),
        "currency": app.get("currency"),
        "rating": app.get("averageUserRating"),
        "ratings_count": app.get("userRatingCount"),
        "version": app.get("version"),
        "last_updated": app.get("currentVersionReleaseDate"),
        "description_snippet": (app.get("description") or "")[:500],
        "genres": app.get("genres", []),
        "content_rating": app.get("contentAdvisoryRating"),
        "min_os": app.get("minimumOsVersion"),
        "size_bytes": app.get("fileSizeBytes"),
        "in_app_purchases": bool(app.get("isGameCenterEnabled")),
        "screenshots_count": len(app.get("screenshotUrls", [])),
    }


def fetch_google_play_info(package_name: str) -> dict | None:
    """Fetch basic info from Google Play store page.

    Uses the public store page — no API key needed.
    Returns limited info compared to iOS.
    """
    url = f"https://play.google.com/store/apps/details?id={package_name}&hl=en&gl=us"

    try:
        resp = retry_httpx_get(url, timeout=15, follow_redirects=True)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        raise

    html_text = resp.text
    json_ld = _extract_google_play_json_ld(html_text)
    meta = _extract_meta_tags(html_text)
    plain_text = _compact_text(html_text)
    rating_data = json_ld.get("aggregateRating", {}) if isinstance(json_ld.get("aggregateRating"), dict) else {}
    offers = json_ld.get("offers", {}) if isinstance(json_ld.get("offers"), dict) else {}

    return {
        "package_name": package_name,
        "store_url": url,
        "available": resp.status_code == 200,
        "name": json_ld.get("name") or meta.get("og:title"),
        "developer": _jsonld_author(json_ld),
        "rating": _to_float(rating_data.get("ratingValue")),
        "ratings_count": _to_int(rating_data.get("ratingCount") or rating_data.get("reviewCount")),
        "price": _to_price(offers.get("price") or meta.get("product:price:amount")),
        "currency": offers.get("priceCurrency") or meta.get("product:price:currency"),
        "version": _find_after_label(plain_text, "Version"),
        "last_updated": _find_after_label(plain_text, "Updated on"),
        "installs": _find_after_label(plain_text, "Downloads") or _find_installs(plain_text),
        "content_rating": _find_after_label(plain_text, "Content rating"),
        "category": json_ld.get("applicationCategory") or _find_after_label(plain_text, "Category"),
        "description_snippet": (meta.get("og:description") or json_ld.get("description") or "")[:500],
    }


def collect_competitor_data(
    competitor_id: str,
    name: str,
    country: str = "us",
) -> dict:
    """Collect all available public data for a competitor app."""
    from datetime import date

    result = {
        "name": name,
        "collected_date": date.today().isoformat(),
        "ios": None,
        "android": None,
    }

    # Try iOS lookup
    ios_data = fetch_ios_app_info(competitor_id, country)
    if ios_data:
        result["ios"] = ios_data

    # Try Google Play lookup (if competitor_id looks like a package name)
    if "." in competitor_id:
        android_data = fetch_google_play_info(competitor_id)
        if android_data:
            result["android"] = android_data

    return result


def write_competitor_data(appagent_dir: Path, competitor_name: str, data: dict) -> Path:
    """Write competitor data to data/competitors/{name}.json."""
    safe_name = competitor_name.lower().replace(" ", "-")
    out_path = appagent_dir / "data" / "competitors" / f"{safe_name}.json"
    atomic_write_json(out_path, data)
    return out_path


def _extract_google_play_json_ld(html_text: str) -> dict:
    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        payload = html.unescape(match.group(1)).strip()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") in {"SoftwareApplication", "MobileApplication"}:
            return data
    return {}


def _extract_meta_tags(html_text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    pattern = re.compile(r"<meta\s+([^>]+)>", flags=re.IGNORECASE)
    for match in pattern.finditer(html_text):
        attrs = _parse_attrs(match.group(1))
        key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
        content = attrs.get("content")
        if key and content:
            meta[key] = html.unescape(content)
    return meta


def _parse_attrs(text: str) -> dict[str, str]:
    attrs = {}
    for key, value in re.findall(r'([:\w-]+)=["\']([^"\']*)["\']', text):
        attrs[key.lower()] = value
    return attrs


def _jsonld_author(data: dict) -> str | None:
    author = data.get("author")
    if isinstance(author, dict):
        return author.get("name")
    if isinstance(author, str):
        return author
    return None


def _compact_text(html_text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _find_after_label(text: str, label: str) -> str | None:
    pattern = rf"{re.escape(label)}\s+([^|•]+?)(?=\s+(?:Updated on|Version|Downloads|Content rating|Category|Contains ads|In-app purchases)\b|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip(" :-")
    return value[:120] if value else None


def _find_installs(text: str) -> str | None:
    match = re.search(r"\b(\d+(?:[,.]\d+)?[KMB]?\+?)\s+downloads\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _to_float(value) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _to_price(value) -> float | None:
    if value in (None, ""):
        return None
    text = str(value).replace(",", "").strip()
    if text.lower() == "free":
        return 0.0
    text = re.sub(r"[^0-9.\-]", "", text)
    return _to_float(text)
