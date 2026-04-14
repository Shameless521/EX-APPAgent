"""Budget ROI tracking — spend logging, ROAS calculation, compliance checks."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from appagent_engine.store.writer import atomic_write_json, atomic_append_jsonl


def budget_log_path(appagent_dir: Path) -> Path:
    return appagent_dir / "data" / "budget" / "log.jsonl"


def append_budget_entry(
    appagent_dir: Path,
    channel: str,
    spend: float,
    attributed_revenue: float = 0.0,
    entry_date: date | None = None,
    note: str = "",
) -> None:
    """Record a budget spend entry."""
    entry = {
        "date": (entry_date or date.today()).isoformat(),
        "channel": channel,
        "spend": round(spend, 2),
        "attributed_revenue": round(attributed_revenue, 2),
        "note": note,
    }
    atomic_append_jsonl(budget_log_path(appagent_dir), entry)


def load_budget_log(appagent_dir: Path) -> list[dict]:
    """Load all budget entries."""
    path = budget_log_path(appagent_dir)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().strip().split("\n"):
        if line:
            entries.append(json.loads(line))
    return entries


def calc_daily_spend(entries: list[dict], target_date: date | None = None) -> float:
    """Calculate total spend for a specific date."""
    if target_date is None:
        target_date = date.today()
    ds = target_date.isoformat()
    return sum(e["spend"] for e in entries if e["date"] == ds)


def calc_roas(entries: list[dict], days: int = 7) -> float | None:
    """Calculate ROAS (Return on Ad Spend) over the last N days.

    ROAS = total attributed revenue / total spend.
    Returns None if no spend recorded.
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    recent = [e for e in entries if e["date"] >= cutoff]

    total_spend = sum(e["spend"] for e in recent)
    total_revenue = sum(e["attributed_revenue"] for e in recent)

    if total_spend == 0:
        return None
    return round(total_revenue / total_spend, 2)


def calc_total_spend(entries: list[dict], days: int = 7) -> float:
    """Calculate total spend over the last N days."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    recent = [e for e in entries if e["date"] >= cutoff]
    return round(sum(e["spend"] for e in recent), 2)


def spend_by_channel(entries: list[dict], days: int = 30) -> dict[str, float]:
    """Break down spend by channel over the last N days."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    recent = [e for e in entries if e["date"] >= cutoff]
    channels: dict[str, float] = {}
    for e in recent:
        ch = e["channel"]
        channels[ch] = channels.get(ch, 0) + e["spend"]
    return {k: round(v, 2) for k, v in sorted(channels.items(), key=lambda x: -x[1])}


def check_budget_compliance(
    entries: list[dict],
    daily_limit: float,
    min_roas: float,
) -> dict:
    """Check if budget usage is within program.md constraints.

    Returns:
        {
            "within_daily_limit": bool,
            "today_spend": float,
            "daily_limit": float,
            "roas_7d": float | None,
            "roas_ok": bool,
            "min_roas": float,
            "total_spend_7d": float,
            "warnings": [str]
        }
    """
    today_spend = calc_daily_spend(entries)
    roas = calc_roas(entries, days=7)
    total_7d = calc_total_spend(entries, days=7)

    warnings = []
    within_limit = today_spend <= daily_limit
    roas_ok = roas is None or roas >= min_roas  # None means no spend, which is fine

    if not within_limit:
        warnings.append(f"Daily spend ${today_spend:.2f} exceeds limit ${daily_limit:.2f}")
    elif today_spend > daily_limit * 0.8:
        warnings.append(f"Daily spend ${today_spend:.2f} is at {today_spend/daily_limit*100:.0f}% of limit")

    if roas is not None and not roas_ok:
        warnings.append(f"7-day ROAS {roas:.2f} is below minimum {min_roas:.2f}")

    return {
        "within_daily_limit": within_limit,
        "today_spend": round(today_spend, 2),
        "daily_limit": daily_limit,
        "roas_7d": roas,
        "roas_ok": roas_ok,
        "min_roas": min_roas,
        "total_spend_7d": total_7d,
        "warnings": warnings,
    }
