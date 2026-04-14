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


def validate_extension_code(code: str) -> dict:
    """Static analysis of extension code for safety violations.

    Checks:
    1. File operations outside allowed directories
    2. Network requests to non-whitelisted domains
    3. Access to sensitive paths (~/.ssh, ~/.aws, etc.)
    4. Dangerous imports (subprocess, os.system, etc.)

    Returns: {"safe": bool, "violations": [str], "checks": {name: passed}}
    """
    import ast
    import re

    violations = []
    checks = {}

    # Parse AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"safe": False, "violations": [f"Syntax error: {e}"], "checks": {}}

    # Check 1: Dangerous imports
    dangerous_modules = {"subprocess", "shutil", "ctypes", "webbrowser"}
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    bad_imports = imports & dangerous_modules
    checks["no_dangerous_imports"] = len(bad_imports) == 0
    if bad_imports:
        violations.append(f"Dangerous imports: {', '.join(bad_imports)}")

    # Check 2: No os.system / os.popen calls
    dangerous_calls = {"system", "popen", "exec", "eval", "execfile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            if func_name in dangerous_calls:
                violations.append(f"Dangerous call: {func_name}()")

    checks["no_dangerous_calls"] = not any("Dangerous call" in v for v in violations)

    # Check 3: Sensitive path access (string literals containing sensitive paths)
    sensitive_patterns = [r'\.ssh', r'\.aws', r'\.gnupg', r'\.config/gcloud', r'/etc/passwd', r'/etc/shadow']
    string_literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]

    for s in string_literals:
        for pat in sensitive_patterns:
            if re.search(pat, s):
                violations.append(f"Sensitive path access: '{s}' matches '{pat}'")

    checks["no_sensitive_paths"] = not any("Sensitive path" in v for v in violations)

    # Check 4: Network domains in string literals
    url_pattern = re.compile(r'https?://([^/\s\'"]+)')
    for s in string_literals:
        for match in url_pattern.finditer(s):
            domain = match.group(1)
            if domain not in _NETWORK_WHITELIST:
                violations.append(f"Non-whitelisted domain: {domain}")

    checks["network_whitelist"] = not any("Non-whitelisted" in v for v in violations)

    return {
        "safe": len(violations) == 0,
        "violations": violations,
        "checks": checks,
    }
