"""Daily metrics assembler — combines platform data into standardized format."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from appagent_engine.store.writer import atomic_write_json


def assemble_daily_metrics(
    report_date: date,
    ios_metrics: dict | None = None,
    android_metrics: dict | None = None,
    reviews_ios: list[dict] | None = None,
    reviews_android: list[dict] | None = None,
    keyword_rankings: dict[str, int] | None = None,
    rating: float | None = None,
    ratings_count: int | None = None,
    active_subscriptions: int | None = None,
) -> dict:
    """Assemble a single daily metrics JSON matching the design spec format.

    Output format:
    {
        "date": "2026-04-12",
        "revenue": 2.3,
        "downloads": 45,
        "rating": 4.6,
        "ratings_count": 234,
        "reviews_new": 3,
        "active_subscriptions": 18,
        "keyword_rankings": {"ringtone maker": 12, ...},
        "platform_breakdown": {
            "ios": {"revenue": 1.5, "downloads": 25},
            "android": {"revenue": 0.8, "downloads": 20}
        }
    }
    """
    ios_rev = ios_metrics.get("revenue", 0) if ios_metrics else 0
    ios_dl = ios_metrics.get("downloads", 0) if ios_metrics else 0
    android_rev = android_metrics.get("revenue", 0) if android_metrics else 0
    android_dl = android_metrics.get("downloads", 0) if android_metrics else 0

    reviews_count = 0
    if reviews_ios:
        reviews_count += len(reviews_ios)
    if reviews_android:
        reviews_count += len(reviews_android)

    result = {
        "date": report_date.isoformat(),
        "revenue": round(ios_rev + android_rev, 2),
        "downloads": ios_dl + android_dl,
        "rating": rating,
        "ratings_count": ratings_count,
        "reviews_new": reviews_count,
        "active_subscriptions": active_subscriptions,
        "keyword_rankings": keyword_rankings or {},
        "platform_breakdown": {
            "ios": {"revenue": round(ios_rev, 2), "downloads": ios_dl},
            "android": {"revenue": round(android_rev, 2), "downloads": android_dl},
        },
    }
    return result


def write_daily_metrics(appagent_dir: Path, metrics: dict) -> Path:
    """Write assembled metrics to data/metrics/YYYY-MM-DD.json."""
    date_str = metrics["date"]
    out_path = appagent_dir / "data" / "metrics" / f"{date_str}.json"
    atomic_write_json(out_path, metrics)
    return out_path
