import argparse
import sys
import time
from pathlib import Path

from . import aggregator, cache, claude_cli, distributor, extractor, git_hook, interview, metrics, repo_meta
from .discovery import discover_repos
from .renderer import render
from .scanner import count_loc, pick_samples, scan_files


def _scan_repo(repo: Path, samples_per_repo: int, model: str | None) -> dict:
    files_by_lang = scan_files(repo)
    entry: dict = {
        "repo": str(repo),
        "repo_name": repo.name,
        "last_commit": repo_meta.last_commit_timestamp(repo),
        "last_scanned": time.time(),
        "languages": {},
    }
    for lang, files in files_by_lang.items():
        loc = count_loc(files)
        if loc == 0:
            continue
        samples = pick_samples(files, n=samples_per_repo)
        rules: list[str] = []
        for s in samples:
            print(f"    [{lang}] sample: {s.relative_to(repo)}")
            rules.extend(extractor.extract_from_sample(s, language=lang, model=model))
        lang_entry: dict = {"loc": loc, "rules": rules}
        if lang == "python":
            file_metrics = [m for f in files if (m := metrics.analyze_file(f)) is not None]
            lang_entry["file_metrics"] = file_metrics
        entry["languages"][lang] = lang_entry
    return entry


def _rebuild_profile(model: str | None, philosophy_path: Path | None = None) -> int:
    cache.prune_missing()
    entries = cache.load_all()
    if not entries:
        print("no cached repos; run `remember-me init` first")
        return 1

    bundles = aggregator.bundles_from_cache(entries)
    per_language: dict[str, dict] = {}
    for lang, bs in bundles.items():
        total_loc = sum(b["loc"] for b in bs)
        if total_loc >= aggregator.MIN_LOC_PER_LANGUAGE:
            per_language[lang] = aggregator.aggregate_language(bs)
        else:
            print(f"skipping {lang}: only {total_loc} LOC")

    if not per_language:
        print("not enough code across cached repos to build a profile")
        return 0

    python_file_metrics = aggregator.flatten_python_ast_metrics(entries)
    python_ast = metrics.aggregate(python_file_metrics) if python_file_metrics else None

    philosophy = interview.load(philosophy_path)
    if philosophy:
        src = philosophy_path or interview.DEFAULT_PATH
        print(f"including philosophy from {src}")

    print(f"synthesizing profile across {len(per_language)} language(s)...")
    content = render(per_language, python_ast=python_ast, model=model, philosophy=philosophy)

    path = distributor.write_profile(content)
    linked = distributor.link_into_claude_md()
    print(f"wrote {path}")
    if linked:
        print(f"linked into {distributor.CLAUDE_MD}")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"error: root not found: {root}", file=sys.stderr)
        return 2
    try:
        claude_cli.ensure_available()
    except claude_cli.ClaudeUnavailable as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"scanning {root} for git repos...")
    repos = discover_repos(root)
    print(f"found {len(repos)} repo(s)")

    for repo in repos:
        current_ts = repo_meta.last_commit_timestamp(repo)
        cached = cache.load(repo)
        if cached and cache.is_fresh(cached, current_ts) and not args.force:
            print(f"  {repo.name}: cache fresh, skipping")
            continue
        print(f"  {repo.name}: scanning")
        entry = _scan_repo(repo, args.samples_per_repo, args.model)
        cache.save(repo, entry)

    return _rebuild_profile(args.model, _philosophy_path(args))


def _cmd_refresh(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists() or not (repo / ".git").is_dir():
        print(f"error: not a git repo: {repo}", file=sys.stderr)
        return 2
    try:
        claude_cli.ensure_available()
    except claude_cli.ClaudeUnavailable as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    current_ts = repo_meta.last_commit_timestamp(repo)
    cached = cache.load(repo)
    if cached and cache.is_fresh(cached, current_ts) and not args.force:
        print(f"{repo.name}: cache fresh, nothing to do")
        return 0

    print(f"{repo.name}: scanning")
    entry = _scan_repo(repo, args.samples_per_repo, args.model)
    cache.save(repo, entry)
    return _rebuild_profile(args.model, _philosophy_path(args))


def _cmd_install_hook(args: argparse.Namespace) -> int:
    ok, msg = git_hook.install(force=args.force)
    print(msg)
    return 0 if ok else 1


def _cmd_rebuild(args: argparse.Namespace) -> int:
    try:
        claude_cli.ensure_available()
    except claude_cli.ClaudeUnavailable as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return _rebuild_profile(args.model, _philosophy_path(args))


def _cmd_interview(args: argparse.Namespace) -> int:
    target = Path(args.output).expanduser().resolve() if args.output else None
    interview.run(output=target)
    return 0


def _philosophy_path(args: argparse.Namespace) -> Path | None:
    """Resolve --philosophy flag if provided; else None (defaults to DEFAULT_PATH)."""
    raw = getattr(args, "philosophy", None)
    return Path(raw).expanduser().resolve() if raw else None


def _cmd_clear(_args: argparse.Namespace) -> int:
    cache.clear_all()
    print("cache cleared")
    return 0


def _cmd_show(_args: argparse.Namespace) -> int:
    profile = distributor.PROFILE
    if not profile.exists():
        print(f"no profile at {profile}; run `remember-me init` first", file=sys.stderr)
        return 1
    print(profile.read_text(encoding="utf-8"))
    return 0


def _cmd_status(_args: argparse.Namespace) -> int:
    entries = cache.load_all()
    print(f"cached repos: {len(entries)}")
    for e in sorted(entries, key=lambda x: -x.get("last_scanned", 0)):
        langs = ", ".join(f"{lang}={data.get('loc', 0)}LOC" for lang, data in e.get("languages", {}).items())
        print(f"  {e.get('repo_name', '?')}: {langs}")
    profile = distributor.PROFILE
    state = "exists" if profile.exists() else "missing"
    print(f"\nprofile: {profile} ({state})")
    current = git_hook._get_current_hooks_path()
    hook_state = "installed" if current == str(git_hook.HOOKS_DIR) else f"not installed (core.hooksPath={current or 'unset'})"
    print(f"git hook: {hook_state}")
    phil_state = "found" if interview.DEFAULT_PATH.exists() else "missing (run `remember-me interview`)"
    print(f"philosophy: {interview.DEFAULT_PATH} ({phil_state})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="remember-me")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="scan your repos and build a style profile")
    init.add_argument("--root", default="~/projects")
    init.add_argument("--samples-per-repo", type=int, default=3)
    init.add_argument("--model", default=None, help="claude model override (e.g. haiku)")
    init.add_argument("--force", action="store_true", help="ignore cache, rescan every repo")
    init.add_argument("--philosophy", default=None, help="path to philosophy markdown (default: ~/.claude/remember-me/philosophy.md if it exists)")
    init.set_defaults(func=_cmd_init)

    refresh = sub.add_parser("refresh", help="re-scan a single repo and rebuild the profile")
    refresh.add_argument("--repo", required=True)
    refresh.add_argument("--samples-per-repo", type=int, default=3)
    refresh.add_argument("--model", default=None)
    refresh.add_argument("--force", action="store_true")
    refresh.add_argument("--philosophy", default=None)
    refresh.set_defaults(func=_cmd_refresh)

    hook = sub.add_parser("install-hook", help="install global git post-commit hook for auto-refresh")
    hook.add_argument("--force", action="store_true", help="override existing core.hooksPath")
    hook.set_defaults(func=_cmd_install_hook)

    status = sub.add_parser("status", help="show what's cached and whether the hook is installed")
    status.set_defaults(func=_cmd_status)

    rebuild = sub.add_parser("rebuild", help="re-synthesize the profile from cache (no rescanning)")
    rebuild.add_argument("--model", default=None)
    rebuild.add_argument("--philosophy", default=None)
    rebuild.set_defaults(func=_cmd_rebuild)

    interview_cmd = sub.add_parser("interview", help="answer questions about how you think — captured into philosophy.md and injected into the profile")
    interview_cmd.add_argument("--output", default=None, help=f"where to write the file (default: {interview.DEFAULT_PATH})")
    interview_cmd.set_defaults(func=_cmd_interview)

    clear = sub.add_parser("clear", help="delete all cached repo + file data")
    clear.set_defaults(func=_cmd_clear)

    show = sub.add_parser("show", help="print the current RememberMe.MD to stdout")
    show.set_defaults(func=_cmd_show)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
