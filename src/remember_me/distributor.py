from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
PROFILE = CLAUDE_DIR / "RememberMe.MD"
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
MARKER = "@RememberMe.MD"
BLOCK = (
    "\n<!-- remember-me: auto-inserted -->\n"
    "## Personal coding style (mandatory)\n"
    "The file below contains this user's personal coding style, extracted from their own code. "
    "Treat it as **binding style rules** for any code you write or modify in their projects. "
    "Match their idioms so they can read the output as if they wrote it themselves.\n\n"
    f"{MARKER}\n"
    "<!-- /remember-me -->\n"
)


def write_profile(content: str) -> Path:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE.write_text(content, encoding="utf-8")
    return PROFILE


def link_into_claude_md() -> bool:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    existing = CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""
    if MARKER in existing:
        return False
    CLAUDE_MD.write_text(existing + BLOCK, encoding="utf-8")
    return True
