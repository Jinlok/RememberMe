import json
from datetime import date

from .claude_cli import ask

_DIRECTIVE = """> **Directive for AI coding assistants.** Treat the patterns below as **binding style rules** for any code you write, modify, or suggest in this user's projects. Match their idioms, naming, structure, error handling, and formatting exactly — including choices that deviate from conventional best practices. The goal: the user must be able to read your output as if they wrote it themselves. When your default behavior would differ from a rule here, **follow the rule**, not your default. If a rule and a user-specific instruction ever conflict, the user's in-conversation instruction wins.

"""

_SYNTHESIS_PROMPT = """You are synthesizing a developer's personal coding style profile.

You have:
1. HARD AST METRICS from the developer's Python code (if any)
2. RAW STYLE RULES extracted from representative sample files per language, sorted with most-relevant first (newer / larger repos weighted higher)

{python_ast_block}

RAW RULES BY LANGUAGE:
{rules_block}

Produce a clean `RememberMe.MD` profile with this structure:

## Meta-Style (language-agnostic)
- 5-8 bullets about philosophy/approach that generalize across languages

{language_section_template}

Rules for your output:
- Remove duplicates and contradictions; prefer the majority / higher-weighted view
- Be specific and actionable — no generic best-practices filler
- Ground every claim in the data (no inventing)
- 5-10 bullets per section max

Return ONLY the markdown content — start with `## Meta-Style`. No preamble."""


def render(per_language: dict[str, dict], python_ast: dict | None = None, model: str | None = None) -> str:
    header = f"# RememberMe Style Profile\n_Auto-generated — last refresh: {date.today().isoformat()}_\n\n"

    if not per_language:
        return header + "_No code found to analyze yet._\n"

    rules_parts = []
    template_parts = []
    for lang, data in per_language.items():
        label = lang.capitalize() if lang != "javascript" else "JavaScript"
        label = "TypeScript" if lang == "typescript" else label
        template_parts.append(f"## {label}\n- bullets specific to {label}")
        rules_parts.append(
            f"### {label} (~{data['loc']} LOC across {data['repos']} repo(s))\n" + "\n".join(data["top_rules"])
        )

    python_ast_block = ""
    if python_ast and python_ast.get("files"):
        python_ast_block = "PYTHON AST METRICS:\n" + json.dumps(python_ast, indent=2, default=str)

    prompt = _SYNTHESIS_PROMPT.format(
        python_ast_block=python_ast_block,
        rules_block="\n\n".join(rules_parts),
        language_section_template="\n\n".join(template_parts),
    )

    try:
        body = ask(prompt, model=model, timeout=240)
    except Exception as e:
        body = f"## Synthesis failed\n\nError: {e}\n\nRaw rules collected:\n\n" + "\n\n".join(
            f"### {lang}\n" + "\n".join(d["top_rules"]) for lang, d in per_language.items()
        )

    return header + _DIRECTIVE + body + "\n"
