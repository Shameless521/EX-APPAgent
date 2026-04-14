"""Configuration management and app registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

GLOBAL_DIR = Path.home() / ".appagent"
CONFIG_PATH = GLOBAL_DIR / "config.json"
APPS_PATH = GLOBAL_DIR / "apps.json"


@dataclass
class AppStoreConnectConfig:
    key_id: str
    issuer_id: str
    private_key_path: Path
    vendor_number: str = ""

    @property
    def private_key(self) -> str:
        return self.private_key_path.expanduser().read_text()


@dataclass
class GooglePlayConfig:
    service_account_path: Path

    @property
    def service_account_info(self) -> dict:
        path = self.service_account_path.expanduser()
        return json.loads(path.read_text())


@dataclass
class CollectionConfig:
    metrics_time: str = "06:00"
    reviews_interval_hours: int = 8


@dataclass
class Config:
    appstore_connect: AppStoreConnectConfig | None = None
    google_play: GooglePlayConfig | None = None
    collection: CollectionConfig = field(default_factory=CollectionConfig)

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> Config:
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text())

        asc = None
        if "appstore_connect" in raw:
            a = raw["appstore_connect"]
            asc = AppStoreConnectConfig(
                key_id=a["key_id"],
                issuer_id=a["issuer_id"],
                private_key_path=Path(a["private_key_path"]),
                vendor_number=a.get("vendor_number", ""),
            )

        gp = None
        if "google_play" in raw:
            g = raw["google_play"]
            gp = GooglePlayConfig(
                service_account_path=Path(g["service_account_path"]),
            )

        coll = CollectionConfig()
        if "collection" in raw:
            c = raw["collection"]
            coll = CollectionConfig(
                metrics_time=c.get("metrics_time", "06:00"),
                reviews_interval_hours=c.get("reviews_interval_hours", 8),
            )

        return cls(appstore_connect=asc, google_play=gp, collection=coll)


def parse_milestones(program_md_path: Path) -> list[dict]:
    """Parse milestones from program.md.

    Returns: [{"target": 1.0, "label": "$1/day", "unlocks": "small ad spend"}, ...]
    """
    if not program_md_path.exists():
        return []

    content = program_md_path.read_text()
    milestones = []
    in_milestones = False

    for line in content.split("\n"):
        stripped = line.strip()
        if "milestones:" in stripped:
            in_milestones = True
            continue
        if in_milestones:
            if stripped.startswith("- "):
                # Parse: "- $1/day → monetization model validated (unlock: small ad spend)"
                text = stripped[2:]
                # Extract target value
                target = _extract_dollar_value(text)
                # Extract label (before →)
                label = text.split("→")[0].strip() if "→" in text else text.split("(")[0].strip()
                # Extract unlocks (after "unlock:" in parentheses)
                unlocks = ""
                if "unlock:" in text.lower():
                    unlocks_part = text.lower().split("unlock:")[1]
                    unlocks = unlocks_part.split(")")[0].strip()
                elif "（" in text and "）" in text:
                    unlocks = text[text.index("（") + 1:text.index("）")]

                if target is not None:
                    milestones.append({
                        "target": target,
                        "label": label,
                        "unlocks": unlocks,
                    })
            elif not stripped.startswith("-") and not stripped.startswith("#"):
                if stripped and not stripped.startswith(" "):
                    break

    return milestones


def _extract_dollar_value(text: str) -> float | None:
    """Extract dollar value from text like '$1/day', '$5/day', '$20/day'."""
    import re
    match = re.search(r'\$(\d+(?:\.\d+)?)', text)
    return float(match.group(1)) if match else None


@dataclass
class AppPlatform:
    bundle_id: str | None = None      # iOS
    package_name: str | None = None   # Android
    store_url: str | None = None


@dataclass
class AppInfo:
    name: str
    path: Path
    registered_at: str | None = None
    ios: AppPlatform | None = None
    android: AppPlatform | None = None
    aso_keywords: list[str] = field(default_factory=list)

    @property
    def appagent_dir(self) -> Path:
        return self.path / ".appagent"


class AppRegistry:
    """Reads and queries ~/.appagent/apps.json."""

    def __init__(self, path: Path = APPS_PATH):
        self._path = path
        self._apps: list[AppInfo] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        raw = json.loads(self._path.read_text())
        for entry in raw.get("apps", []):
            ios = android = None
            platforms = entry.get("platforms", {})
            if "ios" in platforms:
                p = platforms["ios"]
                ios = AppPlatform(
                    bundle_id=p.get("bundle_id"),
                    store_url=p.get("store_url"),
                )
            if "android" in platforms:
                p = platforms["android"]
                android = AppPlatform(
                    package_name=p.get("package_name"),
                    store_url=p.get("store_url"),
                )
            self._apps.append(AppInfo(
                name=entry["name"],
                path=Path(entry["path"]),
                registered_at=entry.get("registered_at"),
                ios=ios,
                android=android,
                aso_keywords=entry.get("aso_keywords", []),
            ))

    @property
    def apps(self) -> list[AppInfo]:
        return list(self._apps)

    def find_by_name(self, name: str) -> AppInfo | None:
        for app in self._apps:
            if app.name.lower() == name.lower():
                return app
        return None

    def find_by_bundle_id(self, bundle_id: str) -> AppInfo | None:
        for app in self._apps:
            if app.ios and app.ios.bundle_id == bundle_id:
                return app
            if app.android and app.android.package_name == bundle_id:
                return app
        return None
