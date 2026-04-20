from pathlib import Path

import pytest

from remember_me import cache


@pytest.fixture(autouse=True)
def redirect_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cache, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(cache, "FILE_RULES_DIR", tmp_path / "file_rules")


def test_save_and_load_round_trip(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    cache.save(repo, {"repo": str(repo), "last_commit": 42, "languages": {}})
    loaded = cache.load(repo)
    assert loaded is not None
    assert loaded["last_commit"] == 42


def test_load_missing_returns_none(tmp_path: Path):
    assert cache.load(tmp_path / "nonexistent") is None


def test_is_fresh():
    assert cache.is_fresh({"last_commit": 100}, 100) is True
    assert cache.is_fresh({"last_commit": 100}, 200) is False
    assert cache.is_fresh(None, 100) is False
    assert cache.is_fresh({"last_commit": 100}, 0) is False


def test_prune_missing_removes_stale_entries(tmp_path: Path):
    alive = tmp_path / "alive"
    alive.mkdir()
    cache.save(alive, {"repo": str(alive)})
    cache.save(tmp_path / "ghost", {"repo": str(tmp_path / "ghost")})

    removed = cache.prune_missing()
    assert removed == 1
    assert cache.load(alive) is not None


def test_file_rules_round_trip(tmp_path: Path):
    src = tmp_path / "sample.py"
    src.write_text("x = 1\n")
    cache.save_file_rules(src, "abc123", ["- rule one", "- rule two"])
    assert cache.load_file_rules(src, "abc123") == ["- rule one", "- rule two"]
    assert cache.load_file_rules(src, "different") is None


def test_clear_all_removes_both_dirs(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    cache.save(repo, {"repo": str(repo)})
    cache.save_file_rules(repo / "f.py", "h", ["- r"])
    cache.clear_all()
    assert not cache.CACHE_DIR.exists()
    assert not cache.FILE_RULES_DIR.exists()
