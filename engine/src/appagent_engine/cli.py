"""CLI entry point — appagent collect / health / daemon."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import click

from appagent_engine.config import Config, AppRegistry

ALL_CATEGORIES = ("metrics", "reviews", "aso", "competitors", "experiments")


@click.group()
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
                    client = AppStoreConnectClient(config.appstore_connect)
                    ios_metrics = client.collect_daily_metrics(app_info.ios.bundle_id, report_date=rd)
                    click.echo(f"  [iOS] Revenue: ${ios_metrics['revenue']}, Downloads: {ios_metrics['downloads']}")
                    health.set_api_status("appstore_connect", "ok")
                except Exception as e:
                    click.echo(f"  [iOS] Error: {e}", err=True)
                    health.set_api_status("appstore_connect", f"error: {e}")
                    health.mark_run_error(f"iOS metrics failed: {e}")

            # Android
            if app_info.android and config.google_play:
                try:
                    from appagent_engine.collectors.googleplay import GooglePlayClient
                    client = GooglePlayClient(config.google_play)
                    android_metrics = client.collect_daily_metrics(app_info.android.package_name, report_date=rd)
                    click.echo(f"  [Android] Reviews: {android_metrics.get('reviews_count', 0)}")
                    health.set_api_status("google_play", "ok")
                except Exception as e:
                    click.echo(f"  [Android] Error: {e}", err=True)
                    health.set_api_status("google_play", f"error: {e}")
                    health.mark_run_error(f"Android metrics failed: {e}")

            # Assemble and write
            metrics = assemble_daily_metrics(report_date=rd, ios_metrics=ios_metrics, android_metrics=android_metrics)
            out_path = write_daily_metrics(appagent_dir, metrics)
            click.echo(f"  Written: {out_path}")

    # --- Reviews ---
    if "reviews" in categories:
        click.echo("\n[Reviews] Fetching...")
        review_count = 0

        if app_info.ios and config.appstore_connect:
            try:
                from appagent_engine.collectors.appstore import AppStoreConnectClient
                from appagent_engine.collectors.reviews import collect_ios_reviews
                client = AppStoreConnectClient(config.appstore_connect)
                app_id = client.get_app_id(app_info.ios.bundle_id)
                if app_id:
                    reviews = collect_ios_reviews(client, app_id)
                    review_count += len(reviews)
                    click.echo(f"  [iOS] {len(reviews)} reviews")
            except Exception as e:
                click.echo(f"  [iOS] Error: {e}", err=True)

        if app_info.android and config.google_play:
            try:
                from appagent_engine.collectors.googleplay import GooglePlayClient
                from appagent_engine.collectors.reviews import collect_android_reviews
                client = GooglePlayClient(config.google_play)
                reviews = collect_android_reviews(client, app_info.android.package_name)
                review_count += len(reviews)
                click.echo(f"  [Android] {len(reviews)} reviews")
            except Exception as e:
                click.echo(f"  [Android] Error: {e}", err=True)

        click.echo(f"  Total: {review_count} reviews")

    # --- ASO ---
    if "aso" in categories and app_info.ios:
        click.echo("\n[ASO] Checking keyword rankings...")
        try:
            from appagent_engine.collectors.aso import check_multiple_keywords, write_aso_data
            keywords = app_info.aso_keywords
            if keywords:
                rankings = check_multiple_keywords(keywords, app_info.ios.bundle_id)
                write_aso_data(appagent_dir, rankings)
                ranked = {k: v for k, v in rankings.items() if v is not None}
                click.echo(f"  Ranked: {ranked or 'none in top 200'}")
            else:
                click.echo("  No keywords configured in apps.json")
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)

    # --- Competitors ---
    if "competitors" in categories:
        click.echo("\n[Competitors] Fetching public data...")
        try:
            from appagent_engine.collectors.competitor import collect_competitor_data, write_competitor_data
            # Read watch_list from program.md
            competitors = _read_competitor_ids(app_info)
            for comp_name, comp_id in competitors:
                data = collect_competitor_data(comp_id, comp_name)
                write_competitor_data(appagent_dir, comp_name, data)
                rating = data.get("ios", {}).get("rating", "?") if data.get("ios") else "?"
                click.echo(f"  {comp_name}: rating {rating}")
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)

    # --- Experiments ---
    if "experiments" in categories:
        click.echo("\n[Experiments] Checking pending...")
        precalcs = process_all_pending(appagent_dir)
        if precalcs:
            click.echo(f"  Pre-calculated {len(precalcs)} experiments")
        else:
            click.echo("  No pending experiments")

    # --- Finalize ---
    health.update_freshness_from_dir(appagent_dir)
    health.mark_run_success()
    health.write()
    click.echo(f"\n✓ Collection complete for {app_info.name}")


def _read_competitor_ids(app_info) -> list[tuple[str, str]]:
    """Extract competitor names and IDs from program.md watch_list."""
    program_path = app_info.path / "program.md"
    if not program_path.exists():
        return []

    content = program_path.read_text()
    competitors = []
    in_watch_list = False
    for line in content.split("\n"):
        line = line.strip()
        if "watch_list:" in line:
            in_watch_list = True
            continue
        if in_watch_list:
            if line.startswith("- "):
                # Extract name and optional bundle_id from parentheses
                name = line[2:].split("(")[0].strip().split("—")[0].strip()
                # Try to extract bundle_id from parentheses
                bundle_id = ""
                if "(" in line and ")" in line:
                    paren = line[line.index("(") + 1:line.index(")")]
                    if "." in paren and " " not in paren:
                        bundle_id = paren
                competitors.append((name, bundle_id or name))
            elif not line.startswith("-") and not line.startswith("#"):
                if line and not line.startswith(" "):
                    break  # End of watch_list section

    return competitors


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
        status_icon = "✓" if status == "ok" else "✗" if status == "error" else "?"
        click.echo(f"  Engine: {status_icon} {status}")
        click.echo(f"  Last run: {engine.get('last_run', 'never')}")
        click.echo(f"  Last success: {engine.get('last_success', 'never')}")

        if engine.get("errors"):
            for err in engine["errors"]:
                click.echo(f"  Error: {err}")

        click.echo(f"  Data freshness:")
        click.echo(f"    Metrics:     {freshness.get('metrics', 'none')}")
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
