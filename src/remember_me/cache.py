import hashlib
import json
import shutil
from pathlib import Path

ROOT_DIR = Path.home() / ".claude" / "remember-me"
CACHE_DIR = ROOT_DIR / "cache"
FILE_RULES_DIR = ROOT_DIR / "file_rules"


def _cache_file(repo: Path) -> Path:
    h = hashlib.sha256(str(repo.resolve()).encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


def _file_rules_key(path: Path, content_hash: str) -> str:
    return hashlib.sha256((str(path.resolve()) + ":" + content_hash).encode()).hexdigest()[:20]


def load_file_rules(path: Path, content_hash: str) -> list[str] | None:
    f = FILE_RULES_DIR / f"{_file_rules_key(path, content_hash)}.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, list) else None


def save_file_rules(path: Path, content_hash: str, rules: list[str]) -> None:
    FILE_RULES_DIR.mkdir(parents=True, exist_ok=True)
    f = FILE_RULES_DIR / f"{_file_rules_key(path, content_hash)}.json"
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(rules), encoding="utf-8")
    tmp.replace(f)


def clear_all() -> None:
    for d in (CACHE_DIR, FILE_RULES_DIR):
        if d.exists():
            shutil.rmtree(d)


def load(repo: Path) -> dict | None:
    f = _cache_file(repo)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save(repo: Path, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = _cache_file(repo)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, default=str), encoding="utf-8")
    tmp.replace(f)


def load_all() -> list[dict]:
    if not CACHE_DIR.exists():
        return []
    entries: list[dict] = []
    for f in CACHE_DIR.glob("*.json"):
        try:
            entries.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return entries


def prune_missing() -> int:
    if not CACHE_DIR.exists():
        return 0
    removed = 0
    for f in CACHE_DIR.glob("*.json"):
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            f.unlink(missing_ok=True)
            removed += 1
            continue
        repo = Path(entry.get("repo", ""))
        if not repo.exists():
            f.unlink(missing_ok=True)
            removed += 1
    return removed


def is_fresh(cached: dict | None, current_commit_ts: float) -> bool:
    if not cached or current_commit_ts <= 0:
        return False
    return cached.get("last_commit", 0) >= current_commit_ts
