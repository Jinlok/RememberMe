# RememberMe

[![CI](https://github.com/Jinlok/RememberMe/actions/workflows/ci.yml/badge.svg)](https://github.com/Jinlok/RememberMe/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

> Extract your personal coding style into a profile that AI coding tools can read.

RememberMe scans your local git repos, samples real code you've written, and synthesizes a binding **style profile** (`~/.claude/RememberMe.MD`) that [Claude Code](https://claude.com/claude-code) uses as coding rules — so generated code reads like *you* wrote it, not like a generic LLM.

It captures things a style guide never does: the fact that you use `const` everywhere but reach for `as any` when it's convenient, that you store money as `_cents` integers, that you write flat `useState` chains instead of `useReducer`, that your Python scripts log with emojis and `"=" * 70` banners.

## How it works

```
 your repos           scanned samples         language bundles        style profile
 ~/projects/*  ──▶    src/remember_me/   ──▶  aggregator.py   ──▶    ~/.claude/
                      extractor.py            per-language            RememberMe.MD
                      (uses claude -p)        idioms                  (binding rules)
```

1. **Discover** — walks a root directory, finds git repos (`discovery.py`)
2. **Scan** — picks representative samples per language (`scanner.py`)
3. **Extract** — asks Claude to pull style rules from each sample (`extractor.py`)
4. **Aggregate** — merges rules across repos into per-language bundles (`aggregator.py`)
5. **Render** — synthesizes the final `RememberMe.MD` (`renderer.py`)
6. **Distribute** — writes the profile and links it into `~/.claude/CLAUDE.md` (`distributor.py`)

Results are cached per repo and refreshed incrementally based on the latest commit timestamp.

## Requirements

- Python **3.11+**
- [Claude Code CLI](https://claude.com/claude-code) (`claude` on your `PATH`) — RememberMe shells out to it for rule extraction
- Git

## Install

```sh
git clone https://github.com/Jinlok/RememberMe.git
cd RememberMe
pip install -e .
```

Or with [uv](https://github.com/astral-sh/uv):

```sh
uv pip install -e .
```

## Usage

### First run

```sh
remember-me init --root ~/projects
```

Scans every git repo under `~/projects`, extracts style rules, writes the profile to `~/.claude/RememberMe.MD`, and links it into `~/.claude/CLAUDE.md` so Claude Code picks it up automatically.

### Keep it fresh on every commit

```sh
remember-me install-hook
```

Installs a global git `post-commit` hook. Each commit silently refreshes the profile for that repo.

> Sets `git config --global core.hooksPath`. Use `--force` to override an existing value.

### Other commands

| Command | What it does |
|---|---|
| `remember-me status` | Show cached repos, LOC per language, profile + hook state |
| `remember-me refresh --repo PATH` | Re-scan a single repo and rebuild the profile |
| `remember-me rebuild` | Re-synthesize the profile from cache (no rescanning) |
| `remember-me show` | Print the current `RememberMe.MD` to stdout |
| `remember-me clear` | Delete all cached repo data |

### Useful flags

- `--model haiku` — use a faster/cheaper Claude model for extraction (default: system default)
- `--samples-per-repo N` — how many files per language per repo to sample (default: 3)
- `--force` — ignore cache and rescan

## What lands in `~/.claude/`

```
~/.claude/
├── CLAUDE.md           # your global Claude Code instructions
│                       #   ↳ gets an auto-inserted block pointing at RememberMe.MD
├── RememberMe.MD       # the generated style profile (binding rules)
└── remember-me/
    ├── cache/          # per-repo scan results (JSON)
    └── hooks/          # post-commit hook (if installed)
```

The link block in `CLAUDE.md` is idempotent — running `init` again won't duplicate it.

## Supported languages

Rule extraction currently covers:

- **JavaScript** (CommonJS / Node scripts)
- **TypeScript** (incl. React / Next.js)
- **Python** (with extra AST-level metrics: function length, nesting depth, early-return rate, etc.)

Each language gets its own section in the final profile, plus a meta-style section that captures cross-cutting habits.

## Development

```sh
pip install -e ".[dev]"
pytest
```

Tests live in `tests/` and cover the scanner, discovery, cache, aggregator, and metrics modules.

## Privacy

RememberMe runs entirely on your machine except for the extraction calls to Claude. Code samples are sent to Claude only during extraction (via the local `claude` CLI). Nothing is uploaded anywhere else. The generated profile is plain text — open `~/.claude/RememberMe.MD` and read it before trusting it.

## License

[MIT](LICENSE)
