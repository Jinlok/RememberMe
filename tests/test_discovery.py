from pathlib import Path

from remember_me import discovery


def test_discover_repos_finds_nested(tmp_path: Path):
    (tmp_path / "foo" / ".git").mkdir(parents=True)
    (tmp_path / "bar" / ".git").mkdir(parents=True)
    (tmp_path / "not_a_repo").mkdir()

    repos = discovery.discover_repos(tmp_path)
    names = {r.name for r in repos}
    assert names == {"foo", "bar"}


def test_discover_repos_skips_heavy_dirs(tmp_path: Path):
    (tmp_path / "node_modules" / "pkg" / ".git").mkdir(parents=True)
    (tmp_path / "real" / ".git").mkdir(parents=True)

    repos = discovery.discover_repos(tmp_path)
    names = {r.name for r in repos}
    assert names == {"real"}


def test_discover_repos_does_not_descend_into_repo(tmp_path: Path):
    (tmp_path / "outer" / ".git").mkdir(parents=True)
    (tmp_path / "outer" / "inner" / ".git").mkdir(parents=True)

    repos = discovery.discover_repos(tmp_path)
    assert len(repos) == 1
    assert repos[0].name == "outer"
