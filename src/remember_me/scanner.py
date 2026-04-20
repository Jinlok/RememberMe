import os
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", ".git", ".next", "target", ".mypy_cache",
    ".pytest_cache", ".tox", ".ruff_cache", ".cache", "migrations",
    "vendor", "out", ".gradle", ".idea", ".vscode",
}

LANGUAGES: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".go": "go",
}

_TEST_SUFFIXES = (".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx",
                  ".test.js", ".spec.js", "_test.go", ".d.ts")


def scan_files(repo: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            ext = Path(fn).suffix
            lang = LANGUAGES.get(ext)
            if lang:
                result[lang].append(Path(dirpath) / fn)
    return dict(result)


def count_loc(files: list[Path]) -> int:
    total = 0
    for f in files:
        try:
            with f.open(encoding="utf-8", errors="ignore") as fp:
                total += sum(1 for _ in fp)
        except OSError:
            continue
    return total


def pick_samples(files: list[Path], n: int = 4) -> list[Path]:
    scored: list[tuple[float, Path]] = []
    for f in files:
        name = f.name.lower()
        if name == "__init__.py" or name.startswith("test_"):
            continue
        if name.endswith(_TEST_SUFFIXES):
            continue
        try:
            with f.open(encoding="utf-8", errors="ignore") as fp:
                loc = sum(1 for _ in fp)
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if loc < 30 or loc > 1000:
            continue
        scored.append((mtime, f))
    scored.sort(reverse=True)
    return [f for _, f in scored[:n]]
