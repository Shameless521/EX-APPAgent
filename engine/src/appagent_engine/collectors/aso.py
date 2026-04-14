"""ASO keyword ranking tracker — uses App Store public search API."""

from __future__ import annotations

from pathlib import Path

import httpx

from appagent_engine.store.writer import atomic_write_json

# App Store public search endpoint (no auth needed)
SEARCH_URL = "https://itunes.apple.com/search"


def check_keyword_rank(
    keyword: str,
    bundle_id: str,
    country: str = "us",
    limit: int = 200,
) -> int | None:
    """Check app's ranking for a keyword in App Store search results.

    Returns rank (1-based) or None if not found in top {limit} results.
    """
    params = {
        "term": keyword,
        "country": country,
        "entity": "software",
        "limit": limit,
    }

    with httpx.Client(timeout=15) as client:
        resp = client.get(SEARCH_URL, params=params)
        resp.raise_for_status()

    results = resp.json().get("results", [])
    for i, app in enumerate(results, 1):
        if app.get("bundleId") == bundle_id:
            return i
    return None


def check_multiple_keywords(
    keywords: list[str],
    bundle_id: str,
    country: str = "us",
) -> dict[str, int | None]:
    """Check rankings for multiple keywords. Returns {keyword: rank}."""
    rankings = {}
    for kw in keywords:
        try:
            rankings[kw] = check_keyword_rank(kw, bundle_id, country)
        except Exception:
            rankings[kw] = None
    return rankings


def write_aso_data(appagent_dir: Path, rankings: dict, keywords_meta: dict | None = None) -> Path:
    """Write ASO data to data/aso/keywords.json."""
    from datetime import date
    out_path = appagent_dir / "data" / "aso" / "keywords.json"
    data = {
        "date": date.today().isoformat(),
        "rankings": rankings,
        "keywords_meta": keywords_meta or {},
    }
    atomic_write_json(out_path, data)
    return out_path
