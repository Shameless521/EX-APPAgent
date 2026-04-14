"""Milestone auto-detection — checks if revenue targets are met for consecutive days."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def check_milestone(
    metrics_dir: Path,
    milestones: list[dict],
    current_stage: str,
    consecutive_days_required: int = 3,
) -> dict:
    """Check if the next milestone has been reached.

    Args:
        metrics_dir: Path to .appagent/data/metrics/
        milestones: Parsed milestone list from program.md
            [{"target": 1.0, "label": "$1/day", "unlocks": "small ad spend"}, ...]
        current_stage: Current stage string, e.g., "from_0_to_1"
        consecutive_days_required: Days revenue must stay above target

    Returns:
        {
            "reached": bool,
            "milestone": {"target": 1.0, "label": "$1/day", "unlocks": "..."},
            "consecutive_days": int,
            "daily_revenues": [float, ...],  # last N days
            "next_stage": str,
        }
    """
    if not metrics_dir.exists():
        return {"reached": False, "milestone": None, "consecutive_days": 0, "daily_revenues": [], "next_stage": current_stage}

    # Find the next milestone based on current stage
    next_milestone = _find_next_milestone(milestones, current_stage)
    if not next_milestone:
        return {"reached": False, "milestone": None, "consecutive_days": 0, "daily_revenues": [], "next_stage": current_stage}

    target = next_milestone["target"]

    # Load recent daily revenues
    files = sorted(metrics_dir.glob("*.json"))
    if not files:
        return {"reached": False, "milestone": next_milestone, "consecutive_days": 0, "daily_revenues": [], "next_stage": current_stage}

    recent_files = files[-consecutive_days_required - 2:]  # Extra buffer
    daily_revenues = []
    for f in recent_files:
        data = json.loads(f.read_text())
        rev = data.get("revenue", 0)
        daily_revenues.append({"date": data.get("date"), "revenue": float(rev) if rev else 0.0})

    # Count consecutive days at or above target (from most recent)
    consecutive = 0
    for entry in reversed(daily_revenues):
        if entry["revenue"] >= target:
            consecutive += 1
        else:
            break

    reached = consecutive >= consecutive_days_required
    next_stage = _compute_next_stage(next_milestone, milestones) if reached else current_stage

    return {
        "reached": reached,
        "milestone": next_milestone,
        "consecutive_days": consecutive,
        "daily_revenues": [e["revenue"] for e in daily_revenues[-consecutive_days_required:]],
        "next_stage": next_stage,
    }


def _find_next_milestone(milestones: list[dict], current_stage: str) -> dict | None:
    """Find the next milestone based on current stage."""
    if not milestones:
        return None

    # Parse current target from stage string (e.g., "from_0_to_1" → target is 1.0)
    # Or "from_1_to_5" → target is 5.0
    try:
        parts = current_stage.split("_to_")
        if len(parts) == 2:
            current_target = float(parts[1])
        else:
            current_target = 0
    except (ValueError, IndexError):
        current_target = 0

    # Find the milestone matching current target
    for ms in milestones:
        if ms["target"] == current_target:
            return ms

    # If no exact match, find the lowest milestone above 0 (first milestone)
    sorted_ms = sorted(milestones, key=lambda m: m["target"])
    for ms in sorted_ms:
        if ms["target"] > current_target:
            return ms

    return sorted_ms[0] if sorted_ms else None


def _compute_next_stage(reached_milestone: dict, all_milestones: list[dict]) -> str:
    """Compute the next stage identifier after reaching a milestone."""
    sorted_ms = sorted(all_milestones, key=lambda m: m["target"])
    reached_target = reached_milestone["target"]

    for i, ms in enumerate(sorted_ms):
        if ms["target"] == reached_target:
            if i + 1 < len(sorted_ms):
                next_target = sorted_ms[i + 1]["target"]
                return f"from_{int(reached_target)}_to_{int(next_target)}"
            else:
                return "target_achieved"

    return "target_achieved"


def write_milestone_pending(appagent_dir: Path, result: dict) -> Path | None:
    """Write milestone_pending.json if a milestone was reached."""
    if not result["reached"]:
        return None

    from appagent_engine.store.writer import atomic_write_json

    path = appagent_dir / "milestone_pending.json"
    atomic_write_json(path, {
        "milestone": result["milestone"],
        "consecutive_days": result["consecutive_days"],
        "daily_revenues": result["daily_revenues"],
        "next_stage": result["next_stage"],
        "detected_at": date.today().isoformat(),
    })
    return path
