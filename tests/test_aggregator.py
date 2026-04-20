import time

from remember_me import aggregator


def test_repo_weight_zero_for_missing_data():
    assert aggregator.repo_weight(0, 1000) == 0.0
    assert aggregator.repo_weight(time.time(), 0) == 0.0


def test_repo_weight_decays_with_age():
    now = time.time()
    fresh = aggregator.repo_weight(now, 1000)
    old = aggregator.repo_weight(now - 365 * 86400, 1000)
    assert fresh > old > 0


def test_repo_weight_scales_with_size():
    now = time.time()
    small = aggregator.repo_weight(now, 100)
    big = aggregator.repo_weight(now, 100_000)
    assert big > small > 0


def test_aggregate_language_sorts_by_weight():
    bundles = [
        {"weight": 0.5, "loc": 100, "rules": ["- low-weight rule"]},
        {"weight": 5.0, "loc": 1000, "rules": ["- high-weight rule"]},
    ]
    result = aggregator.aggregate_language(bundles)
    assert result["loc"] == 1100
    assert result["repos"] == 2
    assert result["top_rules"][0] == "- high-weight rule"


def test_bundles_from_cache():
    now = time.time()
    entries = [
        {
            "last_commit": now,
            "languages": {
                "python": {"loc": 500, "rules": ["- a"]},
                "typescript": {"loc": 200, "rules": ["- b"]},
            },
        },
        {
            "last_commit": now - 10 * 86400,
            "languages": {"python": {"loc": 300, "rules": ["- c"]}},
        },
    ]
    bundles = aggregator.bundles_from_cache(entries)
    assert len(bundles["python"]) == 2
    assert len(bundles["typescript"]) == 1


def test_flatten_python_ast_metrics():
    entries = [
        {"languages": {"python": {"file_metrics": [{"a": 1}, {"a": 2}]}}},
        {"languages": {"python": {"file_metrics": [{"a": 3}]}}},
        {"languages": {"typescript": {"loc": 100}}},
    ]
    assert len(aggregator.flatten_python_ast_metrics(entries)) == 3
