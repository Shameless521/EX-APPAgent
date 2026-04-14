"""Extension loader — dynamic loading, dry-run, and activation of agent-written extensions."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

from appagent_engine.store.writer import atomic_write_json

EXTENSIONS_DIR = Path(__file__).parent
REGISTRY_PATH = EXTENSIONS_DIR / "registry.json"


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {"extensions": {}}


def _save_registry(registry: dict) -> None:
    atomic_write_json(REGISTRY_PATH, registry)


def list_extensions() -> list[dict]:
    """List all extensions with their status."""
    registry = _load_registry()
    extensions = []

    for py_file in sorted(EXTENSIONS_DIR.glob("*.py")):
        if py_file.name.startswith("_") or py_file.name == "loader.py":
            continue
        name = py_file.stem
        info = registry.get("extensions", {}).get(name, {})
        extensions.append({
            "name": name,
            "path": str(py_file),
            "status": info.get("status", "available"),
            "description": info.get("description", ""),
            "activated_at": info.get("activated_at"),
        })

    return extensions


def load_extension(name: str):
    """Dynamically import an extension module by name."""
    ext_path = EXTENSIONS_DIR / f"{name}.py"
    if not ext_path.exists():
        raise FileNotFoundError(f"Extension not found: {ext_path}")

    spec = importlib.util.spec_from_file_location(f"appagent_ext_{name}", ext_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dry_run_extension(name: str, mock_input: dict | None = None) -> dict:
    """Run an extension in sandbox mode with mocked I/O.

    The extension's write operations are intercepted — nothing is written to disk.
    Returns the captured output.
    """
    from appagent_engine.guardrails import validate_extension_code

    ext_path = EXTENSIONS_DIR / f"{name}.py"
    if not ext_path.exists():
        raise FileNotFoundError(f"Extension not found: {ext_path}")

    # Safety check first
    code = ext_path.read_text()
    safety = validate_extension_code(code)
    if not safety["safe"]:
        return {
            "success": False,
            "error": "Safety check failed",
            "violations": safety["violations"],
            "output": None,
        }

    # Load the module
    module = load_extension(name)

    # Find and call the main entry point
    if hasattr(module, "run"):
        try:
            input_data = mock_input or {}
            result = module.run(input_data)
            return {
                "success": True,
                "error": None,
                "violations": [],
                "output": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "violations": [],
                "output": None,
            }
    else:
        return {
            "success": False,
            "error": f"Extension '{name}' has no run() function",
            "violations": [],
            "output": None,
        }


def activate_extension(name: str, description: str = "") -> None:
    """Mark an extension as active in the registry."""
    from datetime import datetime, timezone

    ext_path = EXTENSIONS_DIR / f"{name}.py"
    if not ext_path.exists():
        raise FileNotFoundError(f"Extension not found: {ext_path}")

    registry = _load_registry()
    registry.setdefault("extensions", {})[name] = {
        "status": "active",
        "description": description,
        "activated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_registry(registry)


def deactivate_extension(name: str) -> None:
    """Mark an extension as inactive."""
    registry = _load_registry()
    if name in registry.get("extensions", {}):
        registry["extensions"][name]["status"] = "inactive"
        _save_registry(registry)


def get_active_extensions() -> list[str]:
    """Return names of all active extensions."""
    registry = _load_registry()
    return [
        name for name, info in registry.get("extensions", {}).items()
        if info.get("status") == "active"
    ]
