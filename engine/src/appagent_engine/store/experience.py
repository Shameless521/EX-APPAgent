"""Experience library manager — per-app and global insights by category."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from appagent_engine.config import GLOBAL_DIR
from appagent_engine.store.writer import atomic_write_json

CATEGORIES = ("aso", "pricing", "growth", "product")


def _ensure_experience_file(path: Path) -> list:
    """Load or create an experience file. Returns list of entries."""
    if path.exists():
        return json.loads(path.read_text())
    return []


def read_experience(appagent_dir: Path, category: str) -> list[dict]:
    """Read experience entries for a category (local + global merged)."""
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category: {category}. Must be one of {CATEGORIES}")

    entries = []

    # Local (per-app)
    local_path = appagent_dir / "insights" / f"experience-{category}.json"
    entries.extend(_ensure_experience_file(local_path))

    # Global (cross-app)
    global_path = GLOBAL_DIR / "global-insights" / f"experience-{category}.json"
    entries.extend(_ensure_experience_file(global_path))

    return entries


def append_experience(
    appagent_dir: Path,
    category: str,
    entry: dict,
    cross_app_applicable: bool = False,
) -> None:
    """Add an experience entry to the local file, optionally sync to global."""
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category: {category}. Must be one of {CATEGORIES}")

    # Add metadata
    entry.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    entry.setdefault("category", category)

    # Write to local
    local_path = appagent_dir / "insights" / f"experience-{category}.json"
    entries = _ensure_experience_file(local_path)
    entries.append(entry)
    atomic_write_json(local_path, entries)

    # Sync to global if cross-app applicable
    if cross_app_applicable:
        global_path = GLOBAL_DIR / "global-insights" / f"experience-{category}.json"
        global_entries = _ensure_experience_file(global_path)
        entry["source_app"] = str(appagent_dir.parent.name)
        global_entries.append(entry)
        atomic_write_json(global_path, global_entries)


def count_entries(appagent_dir: Path) -> int:
    """Count total experience entries across all categories (local only)."""
    total = 0
    for cat in CATEGORIES:
        local_path = appagent_dir / "insights" / f"experience-{cat}.json"
        if local_path.exists():
            total += len(json.loads(local_path.read_text()))
    return total
