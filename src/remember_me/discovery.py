import os
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", ".next", "target", ".mypy_cache",
    ".pytest_cache", ".tox", ".ruff_cache", ".cache",
}


def discover_repos(root: Path) -> list[Path]:
    repos: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if (Path(dirpath) / ".git").is_dir():
            repos.append(Path(dirpath))
            dirnames.clear()
    return repos
