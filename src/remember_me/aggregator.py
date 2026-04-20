import math
import time
from collections import defaultdict

MIN_LOC_PER_LANGUAGE = 500
_HALF_LIFE_DAYS = 180
_MAX_RULES_PER_LANGUAGE = 60


def repo_weight(last_commit_ts: float, loc: int) -> float:
    if last_commit_ts <= 0 or loc <= 0:
        return 0.0
    age_days = max(0.0, (time.time() - last_commit_ts) / 86400)
    recency = math.exp(-age_days / _HALF_LIFE_DAYS)
    size = math.log(loc + 1)
    return recency * size


def aggregate_language(bundles: list[dict]) -> dict:
    total_loc = sum(b["loc"] for b in bundles)
    weighted: list[tuple[float, str]] = []
    for b in bundles:
        for rule in b["rules"]:
            weighted.append((b["weight"], rule))
    weighted.sort(key=lambda x: -x[0])
    return {
        "loc": total_loc,
        "repos": len(bundles),
        "top_rules": [r for _, r in weighted[:_MAX_RULES_PER_LANGUAGE]],
    }


def bundles_from_cache(cache_entries: list[dict]) -> dict[str, list[dict]]:
    bundles: dict[str, list[dict]] = defaultdict(list)
    for entry in cache_entries:
        last_commit = entry.get("last_commit", 0)
        for lang, data in entry.get("languages", {}).items():
            loc = data.get("loc", 0)
            if loc <= 0:
                continue
            w = repo_weight(last_commit, loc)
            bundles[lang].append({
                "weight": w,
                "loc": loc,
                "rules": data.get("rules", []),
            })
    return dict(bundles)


def flatten_python_ast_metrics(cache_entries: list[dict]) -> list[dict]:
    out: list[dict] = []
    for e in cache_entries:
        py = e.get("languages", {}).get("python", {})
        out.extend(py.get("file_metrics", []))
    return out
