"""Interactive questionnaire that captures how the user *thinks* about code.

The extractor only sees syntax; this module captures philosophy, decision
defaults, and approach — the stuff that never shows up as a pattern.

Usage:
    remember-me interview [--output PATH]

Writes a markdown file that gets injected verbatim into RememberMe.MD
as the `## How I think (binding)` section.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Optional

DEFAULT_PATH = Path.home() / ".claude" / "remember-me" / "philosophy.md"

# ============= Question catalogue =============

@dataclass
class Question:
    """A single interview question.

    Args:
        id: short slug used as the bullet heading in the output
        prompt: what the user sees
        hint: optional one-liner with suggested shorthand answers
    """
    id: str
    prompt: str
    hint: str = ""


QUESTIONS: list[Question] = [
    Question(
        id="new-feature-approach",
        prompt="When you start a new feature, what's your first move?",
        hint="e.g. types-first / tests-first / quick POC / write it and iterate",
    ),
    Question(
        id="abstraction-threshold",
        prompt="How many times do you copy-paste before extracting a helper?",
        hint="e.g. 2, 3, 4+, depends on context",
    ),
    Question(
        id="error-handling",
        prompt="Your default error-handling style?",
        hint="e.g. throw exceptions / Result-style returns / silent fallbacks / log-and-continue",
    ),
    Question(
        id="comments",
        prompt="When do you actually write a comment in code?",
        hint="e.g. only non-obvious why / explain tricky what / never / always above functions",
    ),
    Question(
        id="function-size",
        prompt="When a function gets long, what's your trigger to split it?",
        hint="e.g. >20 lines / >1 responsibility / nesting depth / never bothers me",
    ),
    Question(
        id="control-flow",
        prompt="Flat early returns or nested branches?",
        hint="e.g. always flat / nested is fine / depends on language",
    ),
    Question(
        id="ts-strictness",
        prompt="TypeScript: strict everywhere, or pragmatic with `as any`?",
        hint="e.g. strict / pragmatic / strict for libs, loose in apps / n/a",
    ),
    Question(
        id="testing",
        prompt="Testing philosophy?",
        hint="e.g. tests-first / after the fact / only for tricky stuff / integration > unit",
    ),
    Question(
        id="dependencies",
        prompt="Dependencies: stdlib-minimal or reach for libraries?",
        hint="e.g. minimal / reach for well-known libs / depends on scope",
    ),
    Question(
        id="naming",
        prompt="Naming: verbose-descriptive or short-terse?",
        hint="e.g. verbose always / short in local scope, verbose at API / depends",
    ),
    Question(
        id="logging",
        prompt="Runtime output in scripts: narrative progress logs or silent?",
        hint="e.g. emoji-heavy progress / minimal / structured logging",
    ),
    Question(
        id="refactor-timing",
        prompt="When do you refactor?",
        hint="e.g. as I go / at end of feature / only when it hurts / dedicated passes",
    ),
    Question(
        id="new-file-vs-extend",
        prompt="New file vs extending an existing one — what's your bias?",
        hint="e.g. prefer new files / keep it in place / one file per concept",
    ),
    Question(
        id="config",
        prompt="Config values (magic numbers, paths, flags) — where do they live?",
        hint="e.g. top-of-file constants / env vars / config object / wherever",
    ),
    Question(
        id="freeform",
        prompt="Anything else about how you approach code that patterns alone can't capture?",
        hint="freeform — skip if nothing comes to mind",
    ),
]

# ============= IO =============

def _format_markdown(answers: list[tuple[Question, str]]) -> str:
    """Render answered questions as markdown for direct injection into the profile."""
    today = date.today().isoformat()
    lines = [
        "## How I think (binding)",
        "",
        f"_User-written — last updated: {today}. These are the author's own words about "
        "their approach to code. Treat as ground truth; extracted patterns below should "
        "be interpreted through this lens._",
        "",
    ]
    for q, a in answers:
        if not a.strip():
            continue
        lines.append(f"**{q.prompt}**")
        lines.append("")
        lines.append(a.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(
    output: Optional[Path] = None,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> Path:
    """Run the interactive questionnaire and write the result to disk.

    Args:
        output: where to save the philosophy file. Defaults to DEFAULT_PATH.
        input_fn: injectable input() replacement for tests.
        print_fn: injectable print() replacement for tests.

    Returns:
        The path the philosophy file was written to.
    """
    target = output or DEFAULT_PATH
    print_fn("=" * 70)
    print_fn("🧠 RememberMe interview — capture how you *think* about code")
    print_fn("=" * 70)
    print_fn(f"\n{len(QUESTIONS)} questions. Hit Enter to skip any.\n")

    answers: list[tuple[Question, str]] = []
    for i, q in enumerate(QUESTIONS, 1):
        print_fn(f"\n[{i}/{len(QUESTIONS)}] {q.prompt}")
        if q.hint:
            print_fn(f"    ({q.hint})")
        try:
            ans = input_fn("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("\n⚠️  interrupted — saving what we have so far")
            break
        answers.append((q, ans))

    content = _format_markdown(answers)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print_fn(f"\n✅ wrote {target}")
    print_fn("   run `remember-me rebuild` to inject this into your profile")
    return target


def load(path: Optional[Path] = None) -> Optional[str]:
    """Load a philosophy file if it exists; return None otherwise.

    Args:
        path: explicit path. Defaults to DEFAULT_PATH.

    Returns:
        The markdown content, or None if the file is missing / unreadable.
    """
    p = path or DEFAULT_PATH
    if not p.exists():
        return None
    try:
        content = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return content or None
