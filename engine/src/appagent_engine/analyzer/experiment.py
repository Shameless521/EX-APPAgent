"""Experiment pre-calculator — computes metric deltas, does NOT make verdicts."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from appagent_engine.analyzer.trends import load_metrics_series, _val
from appagent_engine.store.writer import atomic_write_json


def find_pending_experiments(appagent_dir: Path) -> list[dict]:
    """Find experiments whose observation period has ended but have no pre-calc yet."""
    active_path = appagent_dir / "experiments" / "active.json"
    if not active_path.exists():
        return []

    active = json.loads(active_path.read_text())
    experiments = active if isinstance(active, list) else active.get("experiments", [])

    today = date.today()
    pending = []
    for exp in experiments:
        end_date_str = exp.get("observation_end_date")
        if not end_date_str:
            continue
        end_date = date.fromisoformat(end_date_str)
        if end_date > today:
            continue  # Still running

        # Check if pre-calc already exists
        precalc_path = appagent_dir / "experiments" / "pre-calc" / f"{exp['id']}.json"
        if precalc_path.exists():
            continue  # Already calculated

        pending.append(exp)

    return pending


def pre_calculate(
    experiment: dict,
    appagent_dir: Path,
) -> dict:
    """Compute metrics delta for an experiment. Returns pre-calc data (no verdict).

    Output format matches design spec:
    {
        "id": "exp_001",
        "observation_complete": true,
        "metric_before": {"daily_downloads": 30},
        "metric_after": {"daily_downloads": 42},
        "delta_pct": 40,
        "historical_std_dev": 5.2,
        "exceeds_2x_std_dev": true,
        "daily_breakdown": [28, 35, 40, 45, 42, 48, 44],
        "external_events_detected": []
    }
    """
    exp_id = experiment["id"]
    metric_name = experiment.get("metric", experiment.get("success_metric", "downloads"))
    start_date = date.fromisoformat(experiment["observation_start_date"])
    end_date = date.fromisoformat(experiment["observation_end_date"])

    metrics_dir = appagent_dir / "data" / "metrics"
    all_series = load_metrics_series(metrics_dir, days=90)

    # Split into before and during periods
    before = []
    during = []
    for day in all_series:
        day_date = date.fromisoformat(day["date"])
        if day_date < start_date:
            before.append(day)
        elif start_date <= day_date <= end_date:
            during.append(day)

    # Metric before: average of 7 days before experiment start
    before_window = before[-7:] if len(before) >= 7 else before
    metric_before = (
        sum(_val(d, metric_name) for d in before_window) / len(before_window)
        if before_window else 0
    )

    # Metric after: average during observation period
    metric_after = (
        sum(_val(d, metric_name) for d in during) / len(during)
        if during else 0
    )

    # Delta percentage
    delta_pct = (
        round((metric_after - metric_before) / metric_before * 100, 1)
        if metric_before != 0 else 0
    )

    # Historical std dev (from before period)
    before_values = [_val(d, metric_name) for d in before[-30:]]
    hist_std_dev = 0.0
    if len(before_values) >= 2:
        import math
        mean = sum(before_values) / len(before_values)
        variance = sum((x - mean) ** 2 for x in before_values) / (len(before_values) - 1)
        hist_std_dev = round(math.sqrt(variance), 2)

    # Daily breakdown during experiment
    daily_breakdown = [round(_val(d, metric_name), 2) for d in during]

    result = {
        "id": exp_id,
        "observation_complete": True,
        "metric_name": metric_name,
        "metric_before": {metric_name: round(metric_before, 2)},
        "metric_after": {metric_name: round(metric_after, 2)},
        "delta_pct": delta_pct,
        "historical_std_dev": hist_std_dev,
        "exceeds_2x_std_dev": abs(metric_after - metric_before) > 2 * hist_std_dev if hist_std_dev > 0 else False,
        "daily_breakdown": daily_breakdown,
        "external_events_detected": [],  # TODO: detect from news/competitor data
    }

    return result


def write_pre_calc(appagent_dir: Path, precalc: dict) -> Path:
    """Write pre-calculation result to experiments/pre-calc/{id}.json."""
    exp_id = precalc["id"]
    out_path = appagent_dir / "experiments" / "pre-calc" / f"{exp_id}.json"
    atomic_write_json(out_path, precalc)
    return out_path


def process_all_pending(appagent_dir: Path) -> list[dict]:
    """Find and pre-calculate all pending experiments. Returns list of pre-calc results."""
    pending = find_pending_experiments(appagent_dir)
    results = []
    for exp in pending:
        precalc = pre_calculate(exp, appagent_dir)
        write_pre_calc(appagent_dir, precalc)
        results.append(precalc)
    return results
