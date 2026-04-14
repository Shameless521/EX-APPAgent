"""Review sentiment analysis extension — keyword-based, no external NLP dependencies."""

from __future__ import annotations

# Sentiment keyword dictionaries
_POSITIVE = {
    "love", "great", "excellent", "awesome", "amazing", "perfect", "best",
    "fantastic", "wonderful", "good", "nice", "helpful", "easy", "simple",
    "beautiful", "useful", "recommend", "brilliant", "superb", "smooth",
    "intuitive", "fast", "reliable", "works great", "five stars", "5 stars",
    "喜欢", "好用", "方便", "推荐", "赞", "不错", "好评", "优秀", "满意",
}

_NEGATIVE = {
    "crash", "bug", "broken", "slow", "laggy", "freeze", "error", "terrible",
    "horrible", "worst", "awful", "useless", "waste", "hate", "disappointing",
    "frustrating", "annoying", "expensive", "scam", "ripoff", "refund",
    "not working", "doesn't work", "can't use", "uninstall", "deleted",
    "闪退", "崩溃", "卡顿", "太贵", "骗人", "垃圾", "差评", "退款", "卸载",
    "不好用", "有bug", "无法使用",
}

_COMPLAINT_TOPICS = {
    "crash": ["crash", "crashes", "crashing", "闪退", "崩溃"],
    "performance": ["slow", "laggy", "freeze", "lag", "卡顿", "卡"],
    "price": ["expensive", "price", "cost", "overpriced", "太贵", "收费"],
    "ads": ["ads", "ad", "advertisement", "too many ads", "广告"],
    "ui": ["ugly", "confusing", "hard to use", "interface", "界面"],
    "feature_missing": ["wish", "missing", "need", "should", "希望", "缺少"],
}

_PRAISE_TOPICS = {
    "ease_of_use": ["easy", "simple", "intuitive", "user friendly", "好用", "方便"],
    "quality": ["great", "excellent", "quality", "professional", "专业"],
    "value": ["worth", "value", "free", "affordable", "值得"],
    "design": ["beautiful", "clean", "elegant", "design", "好看", "漂亮"],
    "features": ["feature", "powerful", "useful", "function", "功能"],
}


def run(input_data: dict) -> dict:
    """Main entry point for the extension.

    Args:
        input_data: {"reviews": [{"body": "...", "rating": 4}, ...]}

    Returns:
        {
            "total": int,
            "positive": int,
            "negative": int,
            "neutral": int,
            "avg_rating": float,
            "top_complaints": [{"topic": str, "count": int, "examples": [str]}],
            "top_praises": [{"topic": str, "count": int, "examples": [str]}],
            "sentiment_distribution": {"1": int, "2": int, "3": int, "4": int, "5": int},
        }
    """
    reviews = input_data.get("reviews", [])
    if not reviews:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0}

    positive = 0
    negative = 0
    neutral = 0
    rating_dist = {str(i): 0 for i in range(1, 6)}
    complaint_counts: dict[str, list[str]] = {k: [] for k in _COMPLAINT_TOPICS}
    praise_counts: dict[str, list[str]] = {k: [] for k in _PRAISE_TOPICS}
    total_rating = 0.0
    rated = 0

    for review in reviews:
        body = (review.get("body") or "").lower()
        rating = review.get("rating")

        # Sentiment classification
        pos_hits = sum(1 for w in _POSITIVE if w in body)
        neg_hits = sum(1 for w in _NEGATIVE if w in body)

        if rating:
            rating_dist[str(min(max(int(rating), 1), 5))] += 1
            total_rating += float(rating)
            rated += 1

        if neg_hits > pos_hits or (rating and int(rating) <= 2):
            negative += 1
        elif pos_hits > neg_hits or (rating and int(rating) >= 4):
            positive += 1
        else:
            neutral += 1

        # Topic extraction
        snippet = (review.get("body") or "")[:80]
        for topic, keywords in _COMPLAINT_TOPICS.items():
            if any(kw in body for kw in keywords):
                if len(complaint_counts[topic]) < 3:  # Keep max 3 examples
                    complaint_counts[topic].append(snippet)

        for topic, keywords in _PRAISE_TOPICS.items():
            if any(kw in body for kw in keywords):
                if len(praise_counts[topic]) < 3:
                    praise_counts[topic].append(snippet)

    # Sort topics by count
    top_complaints = sorted(
        [{"topic": k, "count": len(v), "examples": v} for k, v in complaint_counts.items() if v],
        key=lambda x: -x["count"],
    )
    top_praises = sorted(
        [{"topic": k, "count": len(v), "examples": v} for k, v in praise_counts.items() if v],
        key=lambda x: -x["count"],
    )

    return {
        "total": len(reviews),
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "avg_rating": round(total_rating / rated, 1) if rated else None,
        "top_complaints": top_complaints[:5],
        "top_praises": top_praises[:5],
        "sentiment_distribution": rating_dist,
    }
