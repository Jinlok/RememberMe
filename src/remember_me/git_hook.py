import stat
import subprocess
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "remember-me" / "hooks"
POST_COMMIT = HOOKS_DIR / "post-commit"

_HOOK_SCRIPT = """#!/bin/sh
# remember-me post-commit hook — auto-refreshes ~/.claude/RememberMe.MD
if command -v remember-me >/dev/null 2>&1; then
  ( remember-me refresh --repo "$(git rev-parse --show-toplevel 2>/dev/null)" >/dev/null 2>&1 & )
fi
exit 0
"""


def _get_current_hooks_path() -> str | None:
    try:
        r = subprocess.run(
            ["git", "config", "--global", "--get", "core.hooksPath"],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    val = r.stdout.strip()
    return val or None


def install(force: bool = False) -> tuple[bool, str]:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    POST_COMMIT.write_text(_HOOK_SCRIPT, encoding="utf-8")
    POST_COMMIT.chmod(POST_COMMIT.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    current = _get_current_hooks_path()
    target = str(HOOKS_DIR)

    if current == target:
        return True, f"core.hooksPath already points to {target}"

    if current and not force:
        return False, (
            f"core.hooksPath is already set to {current}. "
            f"Use --force to override, or add the post-commit snippet manually:\n\n{POST_COMMIT}"
        )

    try:
        subprocess.run(
            ["git", "config", "--global", "core.hooksPath", target],
            check=True, capture_output=True, text=True, timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return False, f"failed to set core.hooksPath: {e}"

    return True, f"set git core.hooksPath -> {target}"
