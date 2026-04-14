"""Review collector — unified interface for iOS and Android reviews."""

from __future__ import annotations

from dataclasses import dataclass


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


def _android_timestamp(ts: dict) -> str:
    """Convert Google's Timestamp proto to ISO string."""
    seconds = ts.get("seconds", 0)
    if seconds:
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(int(seconds), tz=timezone.utc)
        return dt.isoformat()
    return ""
