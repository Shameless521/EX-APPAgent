"""CLI entry point — appagent collect / health / daemon."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import click

from appagent_engine.config import Config, AppRegistry


@click.group()
def main():
    """EX-APPAgent Data Engine — automated app metrics collection."""
    pass


@main.command()
@click.option("--app", help="App name to collect for (default: all)")
@click.option("--date", "report_date", help="Report date YYYY-MM-DD (default: T-2 for iOS)")
def collect(app: str | None, report_date: str | None):
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

    rd = date.fromisoformat(report_date) if report_date else None

    for app_info in apps:
        click.echo(f"\n{'='*50}")
        click.echo(f"Collecting: {app_info.name}")
        click.echo(f"{'='*50}")
        _collect_one_app(config, app_info, rd)


def _collect_one_app(config: Config, app_info, report_date: date | None):
    """Run full collection pipeline for a single app."""
    from appagent_engine.health import HealthReporter
    from appagent_engine.collectors.assembler import assemble_daily_metrics, write_daily_metrics
    from appagent_engine.analyzer.experiment import process_all_pending

    appagent_dir = app_info.appagent_dir
    health = HealthReporter(appagent_dir)
    health.mark_run_start()

    ios_metrics = None
    android_metrics = None
    reviews_ios = []
    reviews_android = []

    # --- iOS Collection ---
    if app_info.ios and config.appstore_connect:
        click.echo("\n[iOS] Connecting to App Store Connect...")
        try:
            from appagent_engine.collectors.appstore import AppStoreConnectClient
            client = AppStoreConnectClient(config.appstore_connect)

            # Sales data
            click.echo("[iOS] Fetching sales report...")
            ios_metrics = client.collect_daily_metrics(
                app_info.ios.bundle_id,
                report_date=report_date,
            )
            click.echo(f"[iOS] Revenue: ${ios_metrics['revenue']}, Downloads: {ios_metrics['downloads']}")

            # Reviews
            click.echo("[iOS] Fetching reviews...")
            app_id = client.get_app_id(app_info.ios.bundle_id)
            if app_id:
                from appagent_engine.collectors.reviews import collect_ios_reviews
                reviews_ios = collect_ios_reviews(client, app_id)
                click.echo(f"[iOS] {len(reviews_ios)} reviews fetched")

            health.set_api_status("appstore_connect", "ok")
        except Exception as e:
            click.echo(f"[iOS] Error: {e}", err=True)
            health.set_api_status("appstore_connect", f"error: {e}")
            health.mark_run_error(f"iOS collection failed: {e}")

    # --- Android Collection ---
    if app_info.android and config.google_play:
        click.echo("\n[Android] Connecting to Google Play...")
        try:
            from appagent_engine.collectors.googleplay import GooglePlayClient
            client = GooglePlayClient(config.google_play)

            click.echo("[Android] Fetching metrics...")
            android_metrics = client.collect_daily_metrics(
                app_info.android.package_name,
                report_date=report_date,
            )
            click.echo(f"[Android] Reviews: {android_metrics.get('reviews_count', 0)}")

            # Reviews
            click.echo("[Android] Fetching reviews...")
            from appagent_engine.collectors.reviews import collect_android_reviews
            reviews_android = collect_android_reviews(client, app_info.android.package_name)
            click.echo(f"[Android] {len(reviews_android)} reviews fetched")

            health.set_api_status("google_play", "ok")
        except Exception as e:
            click.echo(f"[Android] Error: {e}", err=True)
            health.set_api_status("google_play", f"error: {e}")
            health.mark_run_error(f"Android collection failed: {e}")

    # --- ASO Keywords ---
    if app_info.ios:
        click.echo("\n[ASO] Checking keyword rankings...")
        try:
            from appagent_engine.collectors.aso import check_multiple_keywords, write_aso_data
            # Read keywords from program.md's current focus or competitor watch_list
            keywords = _extract_keywords(app_info)
            if keywords:
                rankings = check_multiple_keywords(keywords, app_info.ios.bundle_id)
                write_aso_data(appagent_dir, rankings)
                ranked = {k: v for k, v in rankings.items() if v is not None}
                click.echo(f"[ASO] Ranked: {ranked or 'none found in top 200'}")
            else:
                click.echo("[ASO] No keywords configured")
        except Exception as e:
            click.echo(f"[ASO] Error: {e}", err=True)

    # --- Assemble Daily Metrics ---
    actual_date = report_date or (date.today() - timedelta(days=2))
    metrics = assemble_daily_metrics(
        report_date=actual_date,
        ios_metrics=ios_metrics,
        android_metrics=android_metrics,
        reviews_ios=[r.to_dict() for r in reviews_ios] if reviews_ios else None,
        reviews_android=[r.to_dict() for r in reviews_android] if reviews_android else None,
    )
    out_path = write_daily_metrics(appagent_dir, metrics)
    click.echo(f"\n[Metrics] Written to {out_path}")

    # --- Experiment Pre-calculation ---
    click.echo("\n[Experiments] Checking pending experiments...")
    precalcs = process_all_pending(appagent_dir)
    if precalcs:
        click.echo(f"[Experiments] Pre-calculated {len(precalcs)} experiments")
    else:
        click.echo("[Experiments] No pending experiments")

    # --- Finalize ---
    health.update_freshness_from_dir(appagent_dir)
    health.mark_run_success()
    health.write()
    click.echo(f"\n✓ Collection complete for {app_info.name}")


def _extract_keywords(app_info) -> list[str]:
    """Get ASO keywords from app config (apps.json → aso_keywords field)."""
    return app_info.aso_keywords


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
