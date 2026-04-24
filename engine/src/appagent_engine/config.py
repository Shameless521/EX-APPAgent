"""Configuration management and app registry."""

from __future__ import annotations

import json
import re
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
    reports_bucket: str = ""

    @property
    def service_account_info(self) -> dict:
        path = self.service_account_path.expanduser()
        return json.loads(path.read_text())

    @property
    def normalized_reports_bucket(self) -> str:
        bucket = self.reports_bucket.strip()
        if bucket.startswith("gs://"):
            bucket = bucket[5:]
        return bucket.strip("/")


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
                reports_bucket=g.get("reports_bucket", g.get("cloud_storage_bucket", "")),
            )

        coll = CollectionConfig()
        if "collection" in raw:
            c = raw["collection"]
            coll = CollectionConfig(
                metrics_time=c.get("metrics_time", "06:00"),
                reviews_interval_hours=c.get("reviews_interval_hours", 8),
            )

        return cls(appstore_connect=asc, google_play=gp, collection=coll)


def parse_program_md(program_md_path: Path) -> dict:
    """Parse program.md into top-level sections with scalar and list values.

    The project template is markdown-like, not strict YAML. This parser supports
    headings (`# Budget`), `key: value` lines, and bullet lists under a key.
    """
    if not program_md_path.exists():
        return {}

    sections: dict[str, dict[str, object]] = {"root": {}}
    section = "root"
    current_key: str | None = None

    for raw_line in program_md_path.read_text().splitlines():
        stripped = raw_line.strip()
        if not stripped:
            current_key = None
            continue
        if stripped.startswith("#"):
            section = _normalize_key(stripped.lstrip("#").strip())
            sections.setdefault(section, {})
            current_key = None
            continue
        if stripped.startswith("- ") and current_key:
            value = sections[section].setdefault(current_key, [])
            if isinstance(value, list):
                value.append(stripped[2:].strip())
            continue
        if ":" in stripped and not stripped.startswith("- "):
            key, value = stripped.split(":", 1)
            current_key = _normalize_key(key)
            clean_value = value.strip()
            sections[section][current_key] = clean_value if clean_value else []
            continue
        current_key = None

    return sections


def parse_program_list(program_md_path: Path, key: str, section: str | None = None) -> list[str]:
    parsed = parse_program_md(program_md_path)
    normalized_key = _normalize_key(key)
    sections = [_normalize_key(section)] if section else list(parsed.keys())
    for section_name in sections:
        value = parsed.get(section_name, {}).get(normalized_key)
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str) and value:
            return [value]
    return []


def parse_program_value(
    program_md_path: Path,
    key: str,
    section: str | None = None,
    default: str = "",
) -> str:
    parsed = parse_program_md(program_md_path)
    normalized_key = _normalize_key(key)
    sections = [_normalize_key(section)] if section else list(parsed.keys())
    for section_name in sections:
        value = parsed.get(section_name, {}).get(normalized_key)
        if isinstance(value, str):
            return value
    return default


def parse_budget_constraints(program_md_path: Path) -> dict[str, float]:
    """Parse Budget section constraints with conservative defaults."""
    daily_limit_raw = parse_program_value(program_md_path, "daily_limit", section="budget")
    min_roas_raw = parse_program_value(program_md_path, "min_roas", section="budget")
    return {
        "daily_limit": _extract_max_number(daily_limit_raw, default=10.0),
        "min_roas": _extract_max_number(min_roas_raw, default=1.5),
    }


def parse_watch_list(program_md_path: Path) -> list[dict]:
    """Parse competitors.watch_list into structured competitor entries."""
    entries = []
    for raw in parse_program_list(program_md_path, "watch_list", section="competitors"):
        cleaned = raw.strip()
        name = cleaned.split("—")[0].strip()
        focus = ""
        focus_match = re.search(r"focus:\s*(.+)$", cleaned, flags=re.IGNORECASE)
        if focus_match:
            focus = focus_match.group(1).strip()

        identifier = _extract_store_identifier(cleaned)
        display_name = name.split("(")[0].strip().strip("[]") or cleaned
        entries.append({
            "name": display_name,
            "identifier": identifier or display_name,
            "focus": focus,
            "raw": cleaned,
        })
    return entries


def parse_milestones(program_md_path: Path) -> list[dict]:
    """Parse milestones from program.md.

    Returns: [{"target": 1.0, "label": "$1/day", "unlocks": "small ad spend"}, ...]
    """
    milestones = []
    for text in parse_program_list(program_md_path, "milestones", section="target"):
        target = _extract_dollar_value(text)
        label = text.split("→")[0].strip() if "→" in text else text.split("(")[0].strip()
        unlocks = ""
        if "unlock:" in text.lower():
            unlocks_part = re.split(r"unlock:", text, flags=re.IGNORECASE)[1]
            unlocks = unlocks_part.split(")")[0].strip()
        elif "（" in text and "）" in text:
            unlocks = text[text.index("（") + 1:text.index("）")]

        if target is not None:
            milestones.append({
                "target": target,
                "label": label,
                "unlocks": unlocks,
            })

    return milestones


def _extract_dollar_value(text: str) -> float | None:
    """Extract dollar value from text like '$1/day', '$5/day', '$20/day'."""
    match = re.search(r'\$(\d+(?:\.\d+)?)', text)
    return float(match.group(1)) if match else None


def _extract_max_number(text: str, default: float) -> float:
    values = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text or "")]
    return max(values) if values else default


def _normalize_key(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower()).strip("_")


def _extract_store_identifier(text: str) -> str:
    url_match = re.search(r"https?://\S+", text)
    if url_match:
        url = url_match.group(0).rstrip(")")
        pkg = re.search(r"[?&]id=([A-Za-z0-9_.]+)", url)
        if pkg:
            return pkg.group(1)
        app_id = re.search(r"/id(\d+)", url)
        if app_id:
            return app_id.group(1)

    paren_values = re.findall(r"\(([^)]+)\)", text)
    for value in paren_values:
        value = value.strip()
        if re.match(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+$", value):
            return value
        if value.isdigit():
            return value

    inline = re.search(r"\b([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)\b", text)
    return inline.group(1) if inline else ""


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
