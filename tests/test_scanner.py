from pathlib import Path

from remember_me import scanner


def test_scan_files_splits_by_language(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.ts").write_text("const x = 1;\n")
    (tmp_path / "c.go").write_text("package main\n")
    (tmp_path / "d.md").write_text("ignored\n")

    result = scanner.scan_files(tmp_path)
    assert set(result.keys()) == {"python", "typescript", "go"}
    assert len(result["python"]) == 1


def test_scan_files_skips_heavy_dirs(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("x;\n")
    (tmp_path / "real.js").write_text("x;\n")

    result = scanner.scan_files(tmp_path)
    assert len(result.get("javascript", [])) == 1


def test_pick_samples_filters_and_sorts(tmp_path: Path):
    tiny = tmp_path / "tiny.py"
    tiny.write_text("x = 1\n")
    good = tmp_path / "good.py"
    good.write_text("\n".join([f"x_{i} = {i}" for i in range(100)]))
    test_file = tmp_path / "test_skip.py"
    test_file.write_text("\n".join([f"x_{i} = {i}" for i in range(100)]))

    samples = scanner.pick_samples([tiny, good, test_file], n=5)
    assert samples == [good]


def test_count_loc(tmp_path: Path):
    f = tmp_path / "a.py"
    f.write_text("a\nb\nc\n")
    assert scanner.count_loc([f]) == 3
