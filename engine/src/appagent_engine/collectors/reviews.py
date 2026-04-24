"""Review collector — unified interface for iOS and Android reviews."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from appagent_engine.store.writer import atomic_write_json


@dataclass
class Review:
    """Unified review structure across platforms."""
    id: str
    platform: str          # "ios" or "android"
    rating: int
    title: str | None
    body: str
    reviewer: str | None
    date: str
    language: str | None = None
    territory: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "platform": self.platform,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "reviewer": self.reviewer,
            "date": self.date,
            "language": self.language,
            "territory": self.territory,
        }


def collect_ios_reviews(
    appstore_client,
    app_id: str,
    limit: int = 50,
) -> list[Review]:
    """Fetch iOS reviews via App Store Connect API."""
    raw = appstore_client.fetch_reviews(app_id, limit=limit)
    return [
        Review(
            id=r["id"],
            platform="ios",
            rating=r["rating"],
            title=r.get("title"),
            body=r.get("body", ""),
            reviewer=r.get("reviewer"),
            date=r.get("date", ""),
            territory=r.get("territory"),
        )
        for r in raw
    ]


def collect_android_reviews(
    play_client,
    package_name: str,
) -> list[Review]:
    """Fetch Android reviews via Google Play Developer API."""
    raw = play_client.fetch_reviews(package_name)
    reviews = []
    for r in raw:
        comments = r.get("comments", [])
        if not comments:
            continue
        user_comment = comments[0].get("userComment", {})
        reviews.append(Review(
            id=r.get("reviewId", ""),
            platform="android",
            rating=user_comment.get("starRating", 0),
            title=None,  # Android reviews don't have separate titles
            body=user_comment.get("text", ""),
            reviewer=r.get("authorName"),
            date=_android_timestamp(user_comment.get("lastModified", {})),
            language=user_comment.get("reviewerLanguage"),
        ))
    return reviews


def write_reviews(
    appagent_dir: Path,
    reviews: list[Review],
    report_date: date | None = None,
) -> Path:
    """Merge and persist collected reviews under data/reviews/YYYY-MM-DD.json."""
    report_date = report_date or date.today()
    out_path = appagent_dir / "data" / "reviews" / f"{report_date.isoformat()}.json"
    existing_reviews: list[dict] = []
    if out_path.exists():
        import json
        existing = json.loads(out_path.read_text())
        if isinstance(existing, list):
            existing_reviews = existing
        else:
            existing_reviews = existing.get("reviews", [])

    collected_at = datetime.now(timezone.utc).isoformat()
    merged: dict[str, dict] = {}
    for item in existing_reviews:
        key = _review_key(item)
        if key:
            merged[key] = item
    for review in reviews:
        item = review.to_dict()
        item["collected_at"] = collected_at
        key = _review_key(item)
        if key:
            merged[key] = item

    ordered = sorted(
        merged.values(),
        key=lambda item: item.get("date") or item.get("collected_at") or "",
        reverse=True,
    )
    counts: dict[str, int] = {}
    for item in ordered:
        platform = item.get("platform") or "unknown"
        counts[platform] = counts.get(platform, 0) + 1

    atomic_write_json(out_path, {
        "date": report_date.isoformat(),
        "collected_at": collected_at,
        "count": len(ordered),
        "platform_counts": counts,
        "reviews": ordered,
    })
    return out_path


def _android_timestamp(ts: dict) -> str:
    """Convert Google's Timestamp proto to ISO string."""
    seconds = ts.get("seconds", 0)
    if seconds:
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(int(seconds), tz=timezone.utc)
        return dt.isoformat()
    return ""


def _review_key(item: dict) -> str:
    review_id = str(item.get("id") or "").strip()
    platform = str(item.get("platform") or "").strip()
    if not review_id or not platform:
        return ""
    return f"{platform}:{review_id}"
