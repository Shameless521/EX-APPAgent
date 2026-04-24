"""CLI entry point — appagent collect / health / daemon."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import click

from appagent_engine import __version__
from appagent_engine.config import Config, AppRegistry

ALL_CATEGORIES = ("metrics", "reviews", "aso", "competitors", "experiments")


@click.group()
@click.version_option(version=__version__, prog_name="appagent")
def main():
    """EX-APPAgent Data Engine — automated app metrics collection."""
    pass


@main.command()
@click.option("--app", help="App name to collect for (default: all)")
@click.option("--only", "categories", help="Comma-separated categories: metrics,reviews,aso,competitors,experiments")
@click.option("--dates", help="Comma-separated dates to collect (YYYY-MM-DD), or 'backfill' to auto-fill gaps")
@click.option("--dry-run", is_flag=True, help="Show what would be collected without executing")
def collect(app: str | None, categories: str | None, dates: str | None, dry_run: bool):
    """Run data collection for one or all registered apps."""
    config = Config.load()
    registry = AppRegistry()

    if not registry.apps:
        click.echo("No apps registered. Check ~/.appagent/apps.json")
        sys.exit(1)

    apps = registry.apps
    if app:
        found = registry.find_by_name(app)
        if not found:
            click.echo(f"App '{app}' not found. Registered: {[a.name for a in apps]}")
            sys.exit(1)
        apps = [found]

    # Parse categories
    cats = set(ALL_CATEGORIES)
    if categories:
        cats = {c.strip() for c in categories.split(",") if c.strip() in ALL_CATEGORIES}
        if not cats:
            click.echo(f"Invalid categories. Choose from: {', '.join(ALL_CATEGORIES)}")
            sys.exit(1)

    # Parse dates
    target_dates = None
    if dates == "backfill":
        target_dates = "backfill"
    elif dates:
        target_dates = [date.fromisoformat(d.strip()) for d in dates.split(",")]

    for app_info in apps:
        click.echo(f"\n{'='*50}")
        click.echo(f"Collecting: {app_info.name}")
        click.echo(f"Categories: {', '.join(sorted(cats))}")
        click.echo(f"{'='*50}")

        if dry_run:
            _dry_run_report(app_info, cats, target_dates)
        else:
            _collect_one_app(config, app_info, cats, target_dates)


def _dry_run_report(app_info, categories: set, target_dates):
    """Show what would be collected without executing."""
    appagent_dir = app_info.appagent_dir
    click.echo("\n[Dry Run] Would collect:")

    if "metrics" in categories:
        dates_to_collect = _resolve_dates(appagent_dir, target_dates)
        click.echo(f"  metrics: {[d.isoformat() for d in dates_to_collect]}")

    if "reviews" in categories:
        click.echo(f"  reviews: iOS + Android latest")

    if "aso" in categories:
        keywords = app_info.aso_keywords
        click.echo(f"  aso: {len(keywords)} keywords — {keywords[:3]}{'...' if len(keywords) > 3 else ''}")

    if "competitors" in categories:
        click.echo(f"  competitors: from program.md watch_list")

    if "experiments" in categories:
        active_path = appagent_dir / "experiments" / "active.json"
        has_active = active_path.exists()
        click.echo(f"  experiments: {'check pending' if has_active else 'no active experiments'}")


def _resolve_dates(appagent_dir: Path, target_dates) -> list[date]:
    """Determine which dates to collect metrics for."""
    if isinstance(target_dates, list):
        return target_dates

    # Find the latest available date (T-2 for App Store)
    latest_available = date.today() - timedelta(days=2)

    if target_dates == "backfill":
        # Find the last collected date
        metrics_dir = appagent_dir / "data" / "metrics"
        if metrics_dir.exists():
            existing = sorted(f.stem for f in metrics_dir.glob("*.json"))
            if existing:
                last_date = date.fromisoformat(existing[-1])
                # Collect all missing dates between last and latest_available
                dates = []
                d = last_date + timedelta(days=1)
                while d <= latest_available:
                    dates.append(d)
                    d += timedelta(days=1)
                return dates if dates else [latest_available]

    return [latest_available]


def _collect_one_app(config: Config, app_info, categories: set, target_dates):
    """Run collection pipeline for a single app, respecting category filter."""
    from appagent_engine.health import HealthReporter
    from appagent_engine.collectors.assembler import assemble_daily_metrics, write_daily_metrics
    from appagent_engine.analyzer.experiment import process_all_pending

    appagent_dir = app_info.appagent_dir
    health = HealthReporter(appagent_dir)
    health.mark_run_start()

    # Resolve dates for metrics collection
    dates_to_collect = _resolve_dates(appagent_dir, target_dates) if "metrics" in categories else []
    reviews_cache: dict[str, list] | None = None

    # --- Metrics (per date) ---
    if "metrics" in categories and dates_to_collect:
        for rd in dates_to_collect:
            click.echo(f"\n[Metrics] Collecting {rd.isoformat()}...")
            ios_metrics = None
            android_metrics = None

            # iOS
            if app_info.ios and config.appstore_connect:
                try:
                    from appagent_engine.collectors.appstore import AppStoreConnectClient
                    health.mark_step_attempted("metrics.ios")
                    client = AppStoreConnectClient(config.appstore_connect)
                    ios_metrics = client.collect_daily_metrics(app_info.ios.bundle_id, report_date=rd)
                    _attach_ios_public_rating(ios_metrics, app_info.ios.bundle_id, health)
                    click.echo(f"  [iOS] Revenue: ${ios_metrics['revenue']}, Downloads: {ios_metrics['downloads']}")
                    health.set_api_status("appstore_connect", "ok")
                    health.mark_step_success("metrics.ios")
                except Exception as e:
                    click.echo(f"  [iOS] Error: {e}", err=True)
                    health.set_api_status("appstore_connect", _error_status(e))
                    health.mark_run_error(f"iOS metrics failed: {e}")

            # Android
            if app_info.android and config.google_play:
                try:
                    from appagent_engine.collectors.googleplay import GooglePlayClient
                    health.mark_step_attempted("metrics.android")
                    client = GooglePlayClient(config.google_play)
                    android_metrics = client.collect_daily_metrics(app_info.android.package_name, report_date=rd)
                    revenue = _display_metric(android_metrics.get("revenue"), money=True)
                    downloads = _display_metric(android_metrics.get("downloads"))
                    click.echo(
                        f"  [Android] Revenue: {revenue}, Downloads: {downloads}, "
                        f"Reviews: {android_metrics.get('reviews_count', 0)}"
                    )
                    missing = android_metrics.get("missing_fields", [])
                    if missing:
                        health.set_api_status("google_play", f"partial: missing {', '.join(missing)}")
                        health.mark_run_error(f"Android metrics incomplete: missing {', '.join(missing)}")
                    else:
                        health.set_api_status("google_play", "ok")
                    health.mark_step_success("metrics.android")
                except Exception as e:
                    click.echo(f"  [Android] Error: {e}", err=True)
                    health.set_api_status("google_play", _error_status(e))
                    health.mark_run_error(f"Android metrics failed: {e}")

            if ios_metrics is None and android_metrics is None:
                click.echo("  No platform metrics collected; skipping daily metrics file")
                health.mark_run_error("Metrics failed: no platform metrics collected", fatal=True)
                continue

            if reviews_cache is None:
                reviews_cache = _collect_reviews_for_app(config, app_info, health, appagent_dir, echo=False)

            ios_reviews_for_date = _reviews_on_date(reviews_cache.get("ios", []), rd)
            android_reviews_for_date = _reviews_on_date(reviews_cache.get("android", []), rd)

            # Assemble and write
            metrics = assemble_daily_metrics(
                report_date=rd,
                ios_metrics=ios_metrics,
                android_metrics=android_metrics,
                reviews_ios=[r.to_dict() for r in ios_reviews_for_date],
                reviews_android=[r.to_dict() for r in android_reviews_for_date],
            )
            out_path = write_daily_metrics(appagent_dir, metrics)
            click.echo(f"  Written: {out_path}")
            health.mark_step_success("metrics")

    # --- Reviews ---
    if "reviews" in categories:
        click.echo("\n[Reviews] Fetching...")
        if reviews_cache is None:
            reviews_cache = _collect_reviews_for_app(config, app_info, health, appagent_dir, echo=True)
        else:
            review_count = sum(len(items) for items in reviews_cache.values())
            for platform, reviews in reviews_cache.items():
                label = "iOS" if platform == "ios" else "Android" if platform == "android" else platform
                click.echo(f"  [{label}] {len(reviews)} reviews")
            click.echo(f"  Total: {review_count} reviews")

    # --- ASO ---
    if "aso" in categories and app_info.ios:
        click.echo("\n[ASO] Checking keyword rankings...")
        try:
            from appagent_engine.collectors.aso import check_multiple_keywords, write_aso_data
            keywords = app_info.aso_keywords
            if keywords:
                health.mark_step_attempted("aso")
                rankings = check_multiple_keywords(keywords, app_info.ios.bundle_id)
                write_aso_data(appagent_dir, rankings)
                ranked = {k: v for k, v in rankings.items() if v is not None}
                click.echo(f"  Ranked: {ranked or 'none in top 200'}")
                health.mark_step_success("aso")
            else:
                click.echo("  No keywords configured in apps.json")
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            health.mark_run_error(f"ASO failed: {e}")

    # --- Competitors ---
    if "competitors" in categories:
        click.echo("\n[Competitors] Fetching public data...")
        try:
            from appagent_engine.collectors.competitor import collect_competitor_data, write_competitor_data
            # Read watch_list from program.md
            competitors = _read_competitor_ids(app_info)
            for comp_name, comp_id in competitors:
                health.mark_step_attempted("competitors")
                data = collect_competitor_data(comp_id, comp_name)
                write_competitor_data(appagent_dir, comp_name, data)
                ios_rating = data.get("ios", {}).get("rating") if data.get("ios") else None
                android_rating = data.get("android", {}).get("rating") if data.get("android") else None
                rating = ios_rating or android_rating or "?"
                click.echo(f"  {comp_name}: rating {rating}")
                health.mark_step_success("competitors")
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            health.mark_run_error(f"Competitors failed: {e}")

    # --- Experiments ---
    if "experiments" in categories:
        click.echo("\n[Experiments] Checking pending...")
        precalcs = process_all_pending(appagent_dir)
        if precalcs:
            click.echo(f"  Pre-calculated {len(precalcs)} experiments")
        else:
            click.echo("  No pending experiments")
        health.mark_step_success("experiments")

    # --- Milestone Detection ---
    click.echo("\n[Milestone] Checking...")
    try:
        from appagent_engine.analyzer.milestone import check_milestone, write_milestone_pending
        from appagent_engine.config import parse_milestones
        milestones = parse_milestones(app_info.path / "program.md")
        if milestones:
            # Read current stage from state.json
            state_path = appagent_dir / "state.json"
            current_stage = "from_0_to_1"
            if state_path.exists():
                import json as _json
                state = _json.loads(state_path.read_text())
                current_stage = state.get("stage", {}).get("current", "from_0_to_1")

            metrics_dir = appagent_dir / "data" / "metrics"
            result = check_milestone(metrics_dir, milestones, current_stage)
            if result["reached"]:
                write_milestone_pending(appagent_dir, result)
                ms = result["milestone"]
                click.echo(f"  🎯 MILESTONE REACHED: {ms['label']}! ({result['consecutive_days']} consecutive days)")
                click.echo(f"  Unlocked: {ms['unlocks']}")
            else:
                ms = result["milestone"]
                if ms:
                    click.echo(f"  Next: {ms['label']} ({result['consecutive_days']}/3 consecutive days)")
                else:
                    click.echo("  All milestones achieved!")
        else:
            click.echo("  No milestones configured in program.md")
    except Exception as e:
        click.echo(f"  Error: {e}", err=True)

    # --- Finalize ---
    health.update_freshness_from_dir(appagent_dir)
    health.mark_run_success()
    health.write()
    click.echo(f"\n✓ Collection complete for {app_info.name}")


def _read_competitor_ids(app_info) -> list[tuple[str, str]]:
    """Extract competitor names and IDs from program.md watch_list."""
    from appagent_engine.config import parse_watch_list

    program_path = app_info.path / "program.md"
    return [
        (entry["name"], entry["identifier"])
        for entry in parse_watch_list(program_path)
    ]


def _collect_reviews_for_app(config: Config, app_info, health, appagent_dir: Path, echo: bool) -> dict[str, list]:
    from appagent_engine.collectors.reviews import (
        collect_android_reviews,
        collect_ios_reviews,
        write_reviews,
    )

    reviews_by_platform: dict[str, list] = {"ios": [], "android": []}

    if app_info.ios and config.appstore_connect:
        try:
            from appagent_engine.collectors.appstore import AppStoreConnectClient
            health.mark_step_attempted("reviews.ios")
            client = AppStoreConnectClient(config.appstore_connect)
            app_id = client.get_app_id(app_info.ios.bundle_id)
            if app_id:
                reviews_by_platform["ios"] = collect_ios_reviews(client, app_id)
            health.mark_step_success("reviews.ios")
            if echo:
                click.echo(f"  [iOS] {len(reviews_by_platform['ios'])} reviews")
        except Exception as e:
            if echo:
                click.echo(f"  [iOS] Error: {e}", err=True)
            health.mark_run_error(f"iOS reviews failed: {e}")

    if app_info.android and config.google_play:
        try:
            from appagent_engine.collectors.googleplay import GooglePlayClient
            health.mark_step_attempted("reviews.android")
            client = GooglePlayClient(config.google_play)
            reviews_by_platform["android"] = collect_android_reviews(client, app_info.android.package_name)
            health.mark_step_success("reviews.android")
            if echo:
                click.echo(f"  [Android] {len(reviews_by_platform['android'])} reviews")
        except Exception as e:
            if echo:
                click.echo(f"  [Android] Error: {e}", err=True)
            health.mark_run_error(f"Android reviews failed: {e}")

    all_reviews = reviews_by_platform["ios"] + reviews_by_platform["android"]
    if all_reviews:
        out_path = write_reviews(appagent_dir, all_reviews)
        health.set_data_freshness("reviews", date.today().isoformat())
        health.mark_step_success("reviews")
        if echo:
            click.echo(f"  Written: {out_path}")

    if echo:
        click.echo(f"  Total: {len(all_reviews)} reviews")
    return reviews_by_platform


def _reviews_on_date(reviews: list, report_date: date) -> list:
    date_prefix = report_date.isoformat()
    return [review for review in reviews if (review.date or "").startswith(date_prefix)]


def _attach_ios_public_rating(metrics: dict, bundle_id: str, health) -> None:
    try:
        from appagent_engine.collectors.competitor import fetch_ios_app_info
        info = fetch_ios_app_info(bundle_id)
        if not info:
            return
        metrics["rating"] = info.get("rating")
        metrics["ratings_count"] = info.get("ratings_count")
    except Exception as e:
        health.mark_run_error(f"iOS public rating failed: {e}")


def _display_metric(value, money: bool = False) -> str:
    if value is None:
        return "unknown"
    return f"${float(value):.2f}" if money else str(value)


def _error_status(exc: Exception) -> str:
    from appagent_engine.net import classify_error
    return f"{classify_error(exc)}: {exc}"


@main.command()
def health():
    """Show engine health status and data freshness for all apps."""
    registry = AppRegistry()

    if not registry.apps:
        click.echo("No apps registered.")
        return

    for app_info in registry.apps:
        health_path = app_info.appagent_dir / "health.json"
        click.echo(f"\n{'='*40}")
        click.echo(f"  {app_info.name}")
        click.echo(f"{'='*40}")

        if not health_path.exists():
            click.echo("  Status: No data collected yet")
            continue

        data = json.loads(health_path.read_text())
        engine = data.get("python_engine", {})
        freshness = data.get("data_freshness", {})
        api = data.get("api_status", {})

        status = engine.get("status", "unknown")
        if status == "ok" and engine.get("errors"):
            status = "partial"
        status_icon = "✓" if status == "ok" else "✗" if status == "error" else "!" if status == "partial" else "?"
        click.echo(f"  Engine: {status_icon} {status}")
        click.echo(f"  Last run: {engine.get('last_run', 'never')}")
        click.echo(f"  Last success: {engine.get('last_success', 'never')}")
        if engine.get("last_partial"):
            click.echo(f"  Last partial: {engine.get('last_partial')}")

        if engine.get("errors"):
            for err in engine["errors"]:
                click.echo(f"  Error: {err}")

        click.echo(f"  Data freshness:")
        click.echo(f"    Metrics:     {freshness.get('metrics', 'none')}")
        click.echo(f"    Reviews:     {freshness.get('reviews', 'none')}")
        click.echo(f"    Competitors: {freshness.get('competitors', 'none')}")
        click.echo(f"    ASO:         {freshness.get('aso', 'none')}")

        click.echo(f"  API status:")
        click.echo(f"    App Store Connect: {api.get('appstore_connect', 'not configured')}")
        click.echo(f"    Google Play:       {api.get('google_play', 'not configured')}")

        # Show backfill status
        metrics_dir = app_info.appagent_dir / "data" / "metrics"
        if metrics_dir.exists():
            files = sorted(f.stem for f in metrics_dir.glob("*.json"))
            if files:
                latest_available = (date.today() - timedelta(days=2)).isoformat()
                gap = (date.fromisoformat(latest_available) - date.fromisoformat(files[-1])).days
                if gap > 0:
                    click.echo(f"  Backfill: {gap} day(s) missing (last: {files[-1]}, available: {latest_available})")
                else:
                    click.echo(f"  Backfill: up to date")


@main.group()
def budget():
    """Track ad spend and ROI."""
    pass


@budget.command("add")
@click.option("--app", required=True, help="App name")
@click.option("--channel", required=True, help="Ad channel (e.g., 'Apple Search Ads')")
@click.option("--spend", required=True, type=float, help="Amount spent")
@click.option("--revenue", "attributed_revenue", default=0.0, type=float, help="Revenue attributed to this spend")
@click.option("--date", "entry_date", help="Date YYYY-MM-DD (default: today)")
@click.option("--note", default="", help="Optional note")
def budget_add(app: str, channel: str, spend: float, attributed_revenue: float, entry_date: str | None, note: str):
    """Record a budget spend entry."""
    from appagent_engine.analyzer.budget import append_budget_entry
    registry = AppRegistry()
    app_info = registry.find_by_name(app)
    if not app_info:
        click.echo(f"App '{app}' not found.")
        sys.exit(1)

    d = date.fromisoformat(entry_date) if entry_date else None
    append_budget_entry(app_info.appagent_dir, channel, spend, attributed_revenue, d, note)
    click.echo(f"✓ Recorded: {channel} ${spend:.2f}" + (f" → ${attributed_revenue:.2f} revenue" if attributed_revenue else ""))


@budget.command("status")
@click.option("--app", help="App name (default: all)")
def budget_status(app: str | None):
    """Show budget ROI status."""
    from appagent_engine.analyzer.budget import load_budget_log, check_budget_compliance, spend_by_channel
    registry = AppRegistry()

    apps = registry.apps
    if app:
        found = registry.find_by_name(app)
        if not found:
            click.echo(f"App '{app}' not found.")
            sys.exit(1)
        apps = [found]

    for app_info in apps:
        entries = load_budget_log(app_info.appagent_dir)
        if not entries:
            click.echo(f"\n{app_info.name}: No budget entries recorded")
            continue

        # Read limits from program.md.
        daily_limit = 10.0
        min_roas = 1.5
        program_path = app_info.path / "program.md"
        if program_path.exists():
            from appagent_engine.config import parse_budget_constraints
            constraints = parse_budget_constraints(program_path)
            daily_limit = constraints["daily_limit"]
            min_roas = constraints["min_roas"]

        status = check_budget_compliance(entries, daily_limit, min_roas)
        channels = spend_by_channel(entries)

        click.echo(f"\n{'='*40}")
        click.echo(f"  {app_info.name} — Budget")
        click.echo(f"{'='*40}")
        click.echo(f"  Today: ${status['today_spend']:.2f} / ${status['daily_limit']:.2f} limit")
        click.echo(f"  7-day ROAS: {status['roas_7d']:.2f}x" if status['roas_7d'] else "  7-day ROAS: no spend")
        click.echo(f"  7-day total: ${status['total_spend_7d']:.2f}")

        if channels:
            click.echo(f"  By channel (30d):")
            for ch, amt in channels.items():
                click.echo(f"    {ch}: ${amt:.2f}")

        for w in status["warnings"]:
            click.echo(f"  ⚠ {w}")


@main.command()
@click.argument("action", type=click.Choice(["start", "stop", "status"]), default="start")
def daemon(action: str):
    """Manage scheduled data collection via macOS launchd."""
    from appagent_engine.scheduler import install_launchd, uninstall_launchd, check_launchd_status

    if action == "start":
        install_launchd()
        click.echo("✓ Scheduled collection enabled")
    elif action == "stop":
        uninstall_launchd()
        click.echo("✓ Scheduled collection disabled")
    elif action == "status":
        check_launchd_status()


if __name__ == "__main__":
    main()
