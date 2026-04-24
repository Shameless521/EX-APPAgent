"""Health reporter — writes .appagent/health.json after each collection run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from appagent_engine.store.writer import atomic_write_json


class HealthReporter:
    """Tracks engine run status, data freshness, and API connectivity."""

    def __init__(self, appagent_dir: Path):
        self._path = appagent_dir / "health.json"
        previous = self._load_previous()
        self._status: dict = {
            "python_engine": {
                "last_run": None,
                "last_success": previous.get("python_engine", {}).get("last_success"),
                "last_partial": previous.get("python_engine", {}).get("last_partial"),
                "status": "not_configured",
                "errors": [],
            },
            "data_freshness": {
                "metrics": None,
                "reviews": None,
                "competitors": None,
                "aso": None,
            },
            "api_status": {
                "appstore_connect": "not_configured",
                "google_play": "not_configured",
            },
        }
        self._attempted_steps: set[str] = set()
        self._successful_steps: set[str] = set()
        self._fatal_errors: list[str] = []

    def _load_previous(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def mark_run_start(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._status["python_engine"]["last_run"] = now
        self._status["python_engine"]["status"] = "running"
        self._status["python_engine"]["errors"] = []
        self._attempted_steps.clear()
        self._successful_steps.clear()
        self._fatal_errors.clear()

    def mark_step_attempted(self, step: str) -> None:
        self._attempted_steps.add(step)

    def mark_step_success(self, step: str) -> None:
        self._attempted_steps.add(step)
        self._successful_steps.add(step)

    def mark_run_success(self, step: str | None = None) -> None:
        """Finalize a run or mark one step as successful.

        Existing callers used this as a finalizer. If errors were recorded, the
        final status must be partial/error rather than blindly ok.
        """
        if step:
            self.mark_step_success(step)
            return

        now = datetime.now(timezone.utc).isoformat()
        errors = self._status["python_engine"]["errors"]
        if not errors:
            self._status["python_engine"]["last_success"] = now
            self._status["python_engine"]["status"] = "ok"
        elif self._fatal_errors or (
            self._attempted_steps and not self._successful_steps
        ):
            self._status["python_engine"]["status"] = "error"
        else:
            self._status["python_engine"]["last_partial"] = now
            self._status["python_engine"]["status"] = "partial"

    def mark_run_error(self, error: str, fatal: bool = False) -> None:
        if fatal:
            self._fatal_errors.append(error)
        if error in self._status["python_engine"]["errors"]:
            return
        self._status["python_engine"]["status"] = "error"
        self._status["python_engine"]["errors"].append(error)

    def set_api_status(self, api: str, status: str) -> None:
        """Set status for an API. api: 'appstore_connect' or 'google_play'."""
        self._status["api_status"][api] = status

    def set_data_freshness(self, category: str, date_str: str) -> None:
        """Set freshness date. category: 'metrics', 'reviews', 'competitors', or 'aso'."""
        self._status["data_freshness"][category] = date_str

    def update_freshness_from_dir(self, appagent_dir: Path) -> None:
        """Scan data directories to determine freshness dates."""
        for category, subdir in [
            ("metrics", "data/metrics"),
            ("reviews", "data/reviews"),
            ("competitors", "data/competitors"),
            ("aso", "data/aso"),
        ]:
            data_dir = appagent_dir / subdir
            if not data_dir.exists():
                continue
            files = sorted(data_dir.glob("*.json"), reverse=True)
            if files:
                # Use file stem as date (e.g., 2026-04-12.json -> 2026-04-12)
                # For non-date-named files, use modification time
                stem = files[0].stem
                if len(stem) == 10 and stem[4] == "-":
                    self._status["data_freshness"][category] = stem
                else:
                    from datetime import datetime
                    mtime = files[0].stat().st_mtime
                    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                    self._status["data_freshness"][category] = dt.strftime("%Y-%m-%d")

    def write(self) -> None:
        atomic_write_json(self._path, self._status)
