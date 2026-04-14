"""Competitor public data collector — App Store & Google Play public info."""

from __future__ import annotations

from pathlib import Path

import httpx

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

    with httpx.Client(timeout=15) as client:
        resp = client.get(ITUNES_LOOKUP_URL, params=params)
        resp.raise_for_status()

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

    with httpx.Client(timeout=15, follow_redirects=True) as client:
        try:
            resp = client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            return None

    # Basic presence check — detailed parsing would need HTML parsing
    # For now, return minimal info confirming the app exists
    return {
        "package_name": package_name,
        "store_url": url,
        "available": resp.status_code == 200,
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
