import shutil
import subprocess


class ClaudeUnavailable(RuntimeError):
    pass


def ensure_available() -> None:
    if shutil.which("claude") is None:
        raise ClaudeUnavailable(
            "`claude` binary not found in PATH. Install Claude Code and retry."
        )


def ask(prompt: str, model: str | None = None, timeout: int = 180) -> str:
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"claude exited {result.returncode}: {result.stderr.strip()}")
    return result.stdout.strip()
