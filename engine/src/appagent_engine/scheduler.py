"""macOS launchd scheduler — manages periodic data collection."""

from __future__ import annotations

import plistlib
import subprocess
from pathlib import Path

LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_NAME_COLLECT = "com.appagent.collect"
PLIST_NAME_REVIEWS = "com.appagent.reviews"
LOG_DIR = Path.home() / ".appagent" / "logs"


def _get_appagent_bin() -> str:
    """Find the appagent CLI binary path."""
    # When installed via uv/pip, it's in the venv bin
    engine_dir = Path(__file__).resolve().parent.parent.parent.parent
    venv_bin = engine_dir / ".venv" / "bin" / "appagent"
    if venv_bin.exists():
        return str(venv_bin)
    # Fallback: try PATH
    return "appagent"


def _generate_plist(label: str, command: list[str], interval: int | None = None, hour: int | None = None, minute: int = 0) -> dict:
    """Generate a launchd plist dict."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    plist = {
        "Label": label,
        "ProgramArguments": command,
        "StandardOutPath": str(LOG_DIR / f"{label}.log"),
        "StandardErrorPath": str(LOG_DIR / f"{label}.error.log"),
        "RunAtLoad": False,
    }

    if interval:
        # Run every N seconds
        plist["StartInterval"] = interval
    elif hour is not None:
        # Run at specific time daily
        plist["StartCalendarInterval"] = {"Hour": hour, "Minute": minute}

    return plist


def install_launchd() -> None:
    """Install launchd plists for scheduled collection."""
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    appagent_bin = _get_appagent_bin()

    # Daily metrics collection at 06:00
    collect_plist = _generate_plist(
        label=PLIST_NAME_COLLECT,
        command=[appagent_bin, "collect"],
        hour=6,
        minute=0,
    )
    collect_path = LAUNCH_AGENTS_DIR / f"{PLIST_NAME_COLLECT}.plist"
    with open(collect_path, "wb") as f:
        plistlib.dump(collect_plist, f)

    # Reviews collection every 8 hours
    reviews_plist = _generate_plist(
        label=PLIST_NAME_REVIEWS,
        command=[appagent_bin, "collect"],  # Same command, reviews are part of collect
        interval=8 * 3600,
    )
    reviews_path = LAUNCH_AGENTS_DIR / f"{PLIST_NAME_REVIEWS}.plist"
    with open(reviews_path, "wb") as f:
        plistlib.dump(reviews_plist, f)

    # Load the agents
    subprocess.run(["launchctl", "load", str(collect_path)], check=True)
    subprocess.run(["launchctl", "load", str(reviews_path)], check=True)

    print(f"Installed: {collect_path}")
    print(f"Installed: {reviews_path}")
    print(f"Logs: {LOG_DIR}")


def uninstall_launchd() -> None:
    """Remove launchd plists."""
    for name in [PLIST_NAME_COLLECT, PLIST_NAME_REVIEWS]:
        plist_path = LAUNCH_AGENTS_DIR / f"{name}.plist"
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
            plist_path.unlink()
            print(f"Removed: {plist_path}")
        else:
            print(f"Not found: {plist_path}")


def check_launchd_status() -> None:
    """Check if launchd agents are loaded and show status."""
    for name in [PLIST_NAME_COLLECT, PLIST_NAME_REVIEWS]:
        plist_path = LAUNCH_AGENTS_DIR / f"{name}.plist"
        exists = plist_path.exists()
        print(f"\n{name}:")
        print(f"  Plist: {'✓' if exists else '✗'} {plist_path}")

        if exists:
            result = subprocess.run(
                ["launchctl", "list", name],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(f"  Status: ✓ loaded")
                for line in result.stdout.strip().split("\n"):
                    print(f"    {line}")
            else:
                print(f"  Status: ✗ not loaded")

        # Show recent log
        log_path = LOG_DIR / f"{name}.log"
        if log_path.exists():
            content = log_path.read_text()
            lines = content.strip().split("\n")
            last_lines = lines[-3:] if len(lines) > 3 else lines
            print(f"  Recent log:")
            for line in last_lines:
                print(f"    {line}")
