import subprocess
from pathlib import Path


def last_commit_timestamp(repo: Path) -> float:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 0.0
    if result.returncode != 0 or not result.stdout.strip():
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0
