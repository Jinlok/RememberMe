import hashlib
from pathlib import Path

from . import cache
from .claude_cli import ask

_PROMPT = """You are analyzing a {language} source file to extract the author's personal coding style.

Return a bulleted list of SPECIFIC, ACTIONABLE style rules that another developer (or an AI) would need to follow to write {language} code in this person's style.

Guidelines:
- Focus on idiosyncrasies, NOT generic best practices ("writes clean code" = useless)
- Cite concrete patterns: "uses X instead of Y", "prefers A over B"
- Cover: naming choices, error handling, function structure, commenting philosophy, abstraction level, library preferences, formatting quirks
- Max 8 bullets, one per line, each starting with "- "

File: {path}

```{language}
{code}
```

Return ONLY the bullet list. No preamble, no summary."""


def extract_from_sample(path: Path, language: str, model: str | None = None) -> list[str]:
    try:
        code = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    content_hash = hashlib.sha256(code.encode("utf-8", errors="ignore")).hexdigest()[:16]
    cached = cache.load_file_rules(path, content_hash)
    if cached is not None:
        return cached

    snippet = code[:20_000] if len(code) > 20_000 else code
    prompt = _PROMPT.format(language=language, path=path.name, code=snippet)
    try:
        raw = ask(prompt, model=model)
    except Exception:
        return []
    rules = [ln.strip() for ln in raw.splitlines() if ln.strip().startswith("-")]
    cache.save_file_rules(path, content_hash, rules)
    return rules
