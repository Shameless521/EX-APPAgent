"""System-enforced guardrails — hard-coded safety checks that cannot be bypassed."""

from __future__ import annotations

from pathlib import Path


class GuardrailViolation(Exception):
    """Raised when a system-enforced guardrail is violated."""


# Sensitive paths that must never be accessed
_SENSITIVE_PATHS = {
    ".ssh", ".aws", ".gnupg", ".config/gcloud",
    ".azure", ".kube", ".docker",
}

# Network whitelist: only these domains are allowed
_NETWORK_WHITELIST = {
    # Apple
    "api.appstoreconnect.apple.com",
    "amp-api.apps.apple.com",
    # Google
    "androidpublisher.googleapis.com",
    "www.googleapis.com",
    "oauth2.googleapis.com",
    "storage.googleapis.com",
    "play.google.com",
    # App Store public
    "apps.apple.com",
    "itunes.apple.com",
}


def validate_file_path(path: Path | str, app_project_path: Path | None = None) -> None:
    """Ensure write target is within allowed directories.

    Allowed: .appagent/ within any app project, engine/ within EX-APPAgent,
    and ~/.appagent/ global directory.
    """
    path = Path(path).resolve()
    home = Path.home()

    # Block sensitive home directory paths
    for sensitive in _SENSITIVE_PATHS:
        if path.is_relative_to(home / sensitive):
            raise GuardrailViolation(
                f"Access denied: {path} is in sensitive directory ~/{sensitive}"
            )

    # Allow: ~/.appagent/
    global_dir = home / ".appagent"
    if path.is_relative_to(global_dir):
        return

    # Allow: <app_project>/.appagent/
    if app_project_path:
        appagent_dir = Path(app_project_path).resolve() / ".appagent"
        if path.is_relative_to(appagent_dir):
            return

    # Allow: engine/ directory (for extensions)
    engine_dir = Path(__file__).resolve().parent.parent.parent
    if path.is_relative_to(engine_dir):
        return

    raise GuardrailViolation(
        f"Access denied: {path} is outside allowed directories "
        f"(.appagent/, engine/, ~/.appagent/)"
    )


def validate_budget(amount: float, daily_limit: float) -> None:
    """Ensure spending does not exceed daily budget limit."""
    if amount > daily_limit:
        raise GuardrailViolation(
            f"Budget exceeded: ${amount:.2f} > daily limit ${daily_limit:.2f}"
        )


def validate_network(url: str) -> None:
    """Ensure network request target is in the whitelist."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    if hostname not in _NETWORK_WHITELIST:
        raise GuardrailViolation(
            f"Network access denied: {hostname} is not in whitelist. "
            f"Allowed: {', '.join(sorted(_NETWORK_WHITELIST))}"
        )
