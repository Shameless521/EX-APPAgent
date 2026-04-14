"""Trend analysis — WoW, MoM, rolling std dev, anomaly detection."""

from __future__ import annotations

import json
import math
from pathlib import Path


def load_metrics_series(
    metrics_dir: Path,
    days: int = 30,
) -> list[dict]:
    """Load the most recent N days of daily metrics, sorted oldest-first."""
    if not metrics_dir.exists():
        return []

    files = sorted(metrics_dir.glob("*.json"))
    # Take the last N files
    recent = files[-days:] if len(files) > days else files
    series = []
    for f in recent:
        data = json.loads(f.read_text())
        series.append(data)
    return series


def calc_wow(series: list[dict], metric: str) -> float | None:
    """Calculate Week-over-Week change percentage.

    Compares last 7 days avg vs previous 7 days avg.
    """
    if len(series) < 14:
        return None

    recent_7 = series[-7:]
    prev_7 = series[-14:-7]

    recent_avg = _avg(recent_7, metric)
    prev_avg = _avg(prev_7, metric)

    if prev_avg == 0:
        return None
    return round((recent_avg - prev_avg) / prev_avg * 100, 1)


def calc_mom(series: list[dict], metric: str) -> float | None:
    """Calculate Month-over-Month change percentage.

    Compares last 30 days avg vs previous 30 days avg.
    """
    if len(series) < 60:
        return None

    recent_30 = series[-30:]
    prev_30 = series[-60:-30]

    recent_avg = _avg(recent_30, metric)
    prev_avg = _avg(prev_30, metric)

    if prev_avg == 0:
        return None
    return round((recent_avg - prev_avg) / prev_avg * 100, 1)


def calc_rolling_std_dev(series: list[dict], metric: str, window: int = 30) -> float | None:
    """Calculate rolling standard deviation over a window of days."""
    if len(series) < window:
        return None

    values = [_val(d, metric) for d in series[-window:]]
    return _std_dev(values)


def detect_anomalies(
    series: list[dict],
    metric: str,
    window: int = 30,
    threshold: float = 2.0,
) -> list[dict]:
    """Detect anomalies where value deviates > threshold * std_dev from mean.

    Returns list of anomaly records with date, value, deviation info.
    """
    if len(series) < window + 1:
        return []

    # Calculate mean and std_dev from the window before the check period
    baseline = series[-(window + 7):-7] if len(series) >= window + 7 else series[:window]
    values = [_val(d, metric) for d in baseline]
    mean = sum(values) / len(values)
    std = _std_dev(values)

    if std == 0:
        return []

    anomalies = []
    for day in series[-7:]:
        val = _val(day, metric)
        deviation = abs(val - mean)
        if deviation > threshold * std:
            anomalies.append({
                "date": day.get("date"),
                "metric": metric,
                "value": val,
                "mean": round(mean, 2),
                "std_dev": round(std, 2),
                "deviation_factor": round(deviation / std, 1),
                "direction": "up" if val > mean else "down",
            })

    return anomalies


def generate_trend_summary(
    metrics_dir: Path,
    metrics: list[str] | None = None,
) -> dict:
    """Generate a complete trend summary for an app.

    Returns: {
        "period": "2026-04-01 to 2026-04-14",
        "metrics": {
            "revenue": {"latest": 2.3, "wow": 15.2, "mom": null, "std_dev": 0.8, "anomalies": []},
            ...
        }
    }
    """
    if metrics is None:
        metrics = ["revenue", "downloads", "rating"]

    series = load_metrics_series(metrics_dir, days=60)
    if not series:
        return {"period": None, "metrics": {}}

    result = {
        "period": f"{series[0].get('date')} to {series[-1].get('date')}",
        "data_points": len(series),
        "metrics": {},
    }

    for m in metrics:
        latest_val = _val(series[-1], m) if series else None
        result["metrics"][m] = {
            "latest": latest_val,
            "wow": calc_wow(series, m),
            "mom": calc_mom(series, m),
            "std_dev": calc_rolling_std_dev(series, m),
            "anomalies": detect_anomalies(series, m),
        }

    return result


# --- Helpers ---

def _val(day: dict, metric: str) -> float:
    """Extract a metric value from a daily record, defaulting to 0."""
    v = day.get(metric, 0)
    return float(v) if v is not None else 0.0


def _avg(days: list[dict], metric: str) -> float:
    if not days:
        return 0.0
    return sum(_val(d, metric) for d in days) / len(days)


def _std_dev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return round(math.sqrt(variance), 4)
