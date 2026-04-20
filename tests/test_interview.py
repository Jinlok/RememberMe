from pathlib import Path

from remember_me import interview


def test_questions_have_unique_ids():
    ids = [q.id for q in interview.QUESTIONS]
    assert len(ids) == len(set(ids))


def test_questions_are_non_trivial():
    assert len(interview.QUESTIONS) >= 10
    for q in interview.QUESTIONS:
        assert q.prompt.strip()
        assert q.id.strip()


def test_format_markdown_skips_blank_answers():
    answers = [
        (interview.QUESTIONS[0], "types-first, always"),
        (interview.QUESTIONS[1], ""),
        (interview.QUESTIONS[2], "throw, never Result-style"),
    ]
    md = interview._format_markdown(answers)
    assert "## How I think (binding)" in md
    assert "types-first, always" in md
    assert "throw, never Result-style" in md
    # blank answer dropped
    assert interview.QUESTIONS[1].prompt not in md


def test_run_writes_file_from_scripted_input(tmp_path: Path):
    answers = iter([
        "POC first, then types",
        "3",
        "throw exceptions",
        "",  # skip
        *[""] * (len(interview.QUESTIONS) - 4),
    ])
    out = tmp_path / "philosophy.md"
    logs: list[str] = []

    result = interview.run(output=out, input_fn=lambda _: next(answers), print_fn=logs.append)

    assert result == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "POC first, then types" in content
    assert "throw exceptions" in content
    assert any("wrote" in line for line in logs)


def test_run_handles_keyboard_interrupt(tmp_path: Path):
    def raising_input(_: str) -> str:
        raise KeyboardInterrupt

    out = tmp_path / "philosophy.md"
    interview.run(output=out, input_fn=raising_input, print_fn=lambda _: None)
    assert out.exists()


def test_load_returns_none_when_missing(tmp_path: Path):
    assert interview.load(tmp_path / "nope.md") is None


def test_load_returns_content(tmp_path: Path):
    p = tmp_path / "philosophy.md"
    p.write_text("## How I think\n\nstuff.\n", encoding="utf-8")
    assert interview.load(p) == "## How I think\n\nstuff."


def test_load_returns_none_for_empty_file(tmp_path: Path):
    p = tmp_path / "philosophy.md"
    p.write_text("   \n\n", encoding="utf-8")
    assert interview.load(p) is None
