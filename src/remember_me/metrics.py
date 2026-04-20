import ast
import re
import statistics
from collections import Counter
from pathlib import Path

_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")
_CAMEL = re.compile(r"^[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*$")
_PASCAL = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
_UPPER = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _classify(name: str) -> str:
    stripped = name.lstrip("_")
    if not stripped:
        return "other"
    if _UPPER.match(stripped):
        return "UPPER"
    if _PASCAL.match(stripped):
        return "Pascal"
    if _CAMEL.match(stripped):
        return "camel"
    if _SNAKE.match(stripped):
        return "snake"
    return "other"


def _max_depth(node: ast.AST, depth: int = 0) -> int:
    max_d = depth
    for child in ast.iter_child_nodes(node):
        nested = isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith))
        max_d = max(max_d, _max_depth(child, depth + 1 if nested else depth))
    return max_d


def _has_early_return(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if len(func.body) < 2:
        return False
    for stmt in func.body[:-1]:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Return):
                return True
    return False


def _has_type_hints(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if func.returns is not None:
        return True
    return any(a.annotation is not None for a in func.args.args)


def analyze_file(path: Path) -> dict | None:
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, ValueError):
        return None

    lines = src.splitlines()
    code_lines = sum(1 for ln in lines if ln.strip() and not ln.strip().startswith("#"))
    comment_lines = sum(1 for ln in lines if ln.strip().startswith("#"))

    func_names: Counter[str] = Counter()
    class_names: Counter[str] = Counter()
    var_names: Counter[str] = Counter()
    func_lengths: list[int] = []
    nesting: list[int] = []
    early_returns = 0
    total_funcs = 0
    funcs_with_docstring = 0
    funcs_with_hints = 0
    total_classes = 0
    classes_with_docstring = 0
    try_count = 0
    fstring_count = 0
    format_count = 0
    percent_format_count = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total_funcs += 1
            func_names[_classify(node.name)] += 1
            start = node.lineno
            end = node.end_lineno or start
            func_lengths.append(end - start + 1)
            nesting.append(_max_depth(node))
            if _has_early_return(node):
                early_returns += 1
            if ast.get_docstring(node):
                funcs_with_docstring += 1
            if _has_type_hints(node):
                funcs_with_hints += 1
        elif isinstance(node, ast.ClassDef):
            total_classes += 1
            class_names[_classify(node.name)] += 1
            if ast.get_docstring(node):
                classes_with_docstring += 1
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_names[_classify(target.id)] += 1
        elif isinstance(node, ast.Try):
            try_count += 1
        elif isinstance(node, ast.JoinedStr):
            fstring_count += 1
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                format_count += 1
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                percent_format_count += 1

    return {
        "path": str(path),
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "func_names": dict(func_names),
        "class_names": dict(class_names),
        "var_names": dict(var_names),
        "func_lengths": func_lengths,
        "nesting": nesting,
        "early_returns": early_returns,
        "total_funcs": total_funcs,
        "funcs_with_docstring": funcs_with_docstring,
        "funcs_with_hints": funcs_with_hints,
        "total_classes": total_classes,
        "classes_with_docstring": classes_with_docstring,
        "try_count": try_count,
        "fstring_count": fstring_count,
        "format_count": format_count,
        "percent_format_count": percent_format_count,
    }


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def aggregate(file_metrics: list[dict]) -> dict:
    if not file_metrics:
        return {"files": 0, "loc": 0}

    total_loc = sum(m["code_lines"] for m in file_metrics)
    total_comments = sum(m["comment_lines"] for m in file_metrics)

    func_names: Counter[str] = Counter()
    class_names: Counter[str] = Counter()
    var_names: Counter[str] = Counter()
    for m in file_metrics:
        func_names.update(m["func_names"])
        class_names.update(m["class_names"])
        var_names.update(m["var_names"])

    all_func_lengths = [l for m in file_metrics for l in m["func_lengths"]]
    all_nesting = [n for m in file_metrics for n in m["nesting"]]
    total_funcs = sum(m["total_funcs"] for m in file_metrics)
    total_classes = sum(m["total_classes"] for m in file_metrics)

    return {
        "files": len(file_metrics),
        "loc": total_loc,
        "comment_density": total_comments / max(total_loc, 1),
        "func_naming": dict(func_names),
        "class_naming": dict(class_names),
        "var_naming": dict(var_names),
        "func_length_median": statistics.median(all_func_lengths) if all_func_lengths else 0,
        "func_length_p90": _percentile(all_func_lengths, 90),
        "nesting_median": statistics.median(all_nesting) if all_nesting else 0,
        "nesting_max": max(all_nesting) if all_nesting else 0,
        "early_return_rate": sum(m["early_returns"] for m in file_metrics) / max(total_funcs, 1),
        "docstring_coverage_funcs": sum(m["funcs_with_docstring"] for m in file_metrics) / max(total_funcs, 1),
        "docstring_coverage_classes": sum(m["classes_with_docstring"] for m in file_metrics) / max(total_classes, 1),
        "type_hint_coverage": sum(m["funcs_with_hints"] for m in file_metrics) / max(total_funcs, 1),
        "try_per_100_loc": sum(m["try_count"] for m in file_metrics) / max(total_loc, 1) * 100,
        "fstring_count": sum(m["fstring_count"] for m in file_metrics),
        "format_count": sum(m["format_count"] for m in file_metrics),
        "percent_format_count": sum(m["percent_format_count"] for m in file_metrics),
    }
