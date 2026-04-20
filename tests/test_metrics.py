from pathlib import Path

from remember_me import metrics


def test_analyze_file_basic(tmp_path: Path):
    src = tmp_path / "sample.py"
    src.write_text(
        "def hello_world(x: int) -> str:\n"
        "    if x > 0:\n"
        "        return 'yes'\n"
        "    return 'no'\n"
        "\n"
        "class MyClass:\n"
        "    pass\n"
    )
    result = metrics.analyze_file(src)
    assert result is not None
    assert result["total_funcs"] == 1
    assert result["total_classes"] == 1
    assert result["funcs_with_hints"] == 1
    assert result["early_returns"] == 1
    assert result["func_names"] == {"snake": 1}
    assert result["class_names"] == {"Pascal": 1}


def test_analyze_file_syntax_error(tmp_path: Path):
    src = tmp_path / "broken.py"
    src.write_text("def oops(:\n")
    assert metrics.analyze_file(src) is None


def test_aggregate_empty():
    result = metrics.aggregate([])
    assert result["files"] == 0


def test_aggregate_combines_counts():
    f1 = {
        "code_lines": 10, "comment_lines": 2,
        "func_names": {"snake": 3}, "class_names": {}, "var_names": {"snake": 5},
        "func_lengths": [5, 10], "nesting": [1, 2],
        "early_returns": 1, "total_funcs": 2,
        "funcs_with_docstring": 1, "funcs_with_hints": 2,
        "total_classes": 0, "classes_with_docstring": 0,
        "try_count": 1, "fstring_count": 3,
        "format_count": 0, "percent_format_count": 0,
    }
    f2 = dict(f1)
    f2["func_names"] = {"snake": 1, "camel": 1}
    agg = metrics.aggregate([f1, f2])
    assert agg["files"] == 2
    assert agg["loc"] == 20
    assert agg["func_naming"] == {"snake": 4, "camel": 1}
    assert agg["type_hint_coverage"] == 1.0
