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
    ios_rev = _metric_number(ios_metrics, "revenue") if ios_metrics else None
    ios_dl = _metric_int(ios_metrics, "downloads") if ios_metrics else None
    android_rev = _metric_number(android_metrics, "revenue") if android_metrics else None
    android_dl = _metric_int(android_metrics, "downloads") if android_metrics else None

    reviews_count = 0
    if reviews_ios:
        reviews_count += len(reviews_ios)
    if reviews_android:
        reviews_count += len(reviews_android)
    reviews_provided = reviews_ios is not None or reviews_android is not None
    if not reviews_provided:
        reviews_count += int(ios_metrics.get("reviews_count", 0) if ios_metrics else 0)
        reviews_count += int(android_metrics.get("reviews_count", 0) if android_metrics else 0)

    if rating is None:
        rating = _weighted_rating(ios_metrics, android_metrics)
    if ratings_count is None:
        counts = [
            int(m.get("ratings_count", 0))
            for m in (ios_metrics, android_metrics)
            if m and m.get("ratings_count") is not None
        ]
        ratings_count = sum(counts) if counts else None

    if active_subscriptions is None and android_metrics:
        active_subscriptions = android_metrics.get("active_subscriptions")

    missing_fields = []
    for platform, metrics in (("ios", ios_metrics), ("android", android_metrics)):
        if metrics is None:
            continue
        for field in ("revenue", "downloads"):
            if metrics.get(field) is None:
                missing_fields.append(f"{platform}.{field}")

    result = {
        "date": report_date.isoformat(),
        "revenue": round(sum(v for v in (ios_rev, android_rev) if v is not None), 2),
        "downloads": sum(v for v in (ios_dl, android_dl) if v is not None),
        "rating": rating,
        "ratings_count": ratings_count,
        "reviews_new": reviews_count,
        "active_subscriptions": active_subscriptions,
        "keyword_rankings": keyword_rankings or {},
        "platform_breakdown": {
            "ios": {"revenue": _round_or_none(ios_rev), "downloads": ios_dl},
            "android": {"revenue": _round_or_none(android_rev), "downloads": android_dl},
        },
        "data_quality": {
            "complete": not missing_fields,
            "missing_fields": missing_fields,
        },
    }
    return result


def write_daily_metrics(appagent_dir: Path, metrics: dict) -> Path:
    """Write assembled metrics to data/metrics/YYYY-MM-DD.json."""
    date_str = metrics["date"]
    out_path = appagent_dir / "data" / "metrics" / f"{date_str}.json"
    atomic_write_json(out_path, metrics)
    return out_path


def _metric_number(metrics: dict | None, key: str) -> float | None:
    if not metrics or metrics.get(key) is None:
        return None
    return float(metrics.get(key, 0))


def _metric_int(metrics: dict | None, key: str) -> int | None:
    if not metrics or metrics.get(key) is None:
        return None
    return int(metrics.get(key, 0))


def _round_or_none(value: float | None) -> float | None:
    return round(value, 2) if value is not None else None


def _weighted_rating(ios_metrics: dict | None, android_metrics: dict | None) -> float | None:
    weighted_total = 0.0
    weight = 0
    simple_values = []

    for metrics in (ios_metrics, android_metrics):
        if not metrics:
            continue
        rating = metrics.get("rating", metrics.get("avg_rating"))
        if rating is None:
            continue
        count = metrics.get("ratings_count")
        if count:
            weighted_total += float(rating) * int(count)
            weight += int(count)
        else:
            simple_values.append(float(rating))

    if weight:
        return round(weighted_total / weight, 2)
    if simple_values:
        return round(sum(simple_values) / len(simple_values), 2)
    return None
