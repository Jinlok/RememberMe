from remember_me import renderer


def _fake_ask(_prompt: str, model=None, timeout=240) -> str:
    # stub claude_cli.ask so render() is deterministic in tests
    del model, timeout
    return "## Meta-Style\n- stubbed synthesis\n\n## Python\n- stubbed python bullet"


def test_render_without_data_includes_philosophy(monkeypatch):
    monkeypatch.setattr(renderer, "ask", _fake_ask)
    out = renderer.render({}, philosophy="## How I think (binding)\n\nI write types first.")
    assert "# RememberMe Style Profile" in out
    assert "I write types first." in out
    assert "No code found" in out


def test_render_injects_philosophy_before_body(monkeypatch):
    monkeypatch.setattr(renderer, "ask", _fake_ask)
    per_lang = {"python": {"loc": 2000, "repos": 2, "top_rules": ["- rule a", "- rule b"]}}
    philosophy = "## How I think (binding)\n\nI throw exceptions."

    out = renderer.render(per_lang, philosophy=philosophy)

    phil_idx = out.index("I throw exceptions.")
    meta_idx = out.index("## Meta-Style")
    assert phil_idx < meta_idx


def test_render_without_philosophy_is_unchanged(monkeypatch):
    monkeypatch.setattr(renderer, "ask", _fake_ask)
    per_lang = {"python": {"loc": 2000, "repos": 2, "top_rules": ["- rule a"]}}
    out = renderer.render(per_lang, philosophy=None)
    assert "How I think" not in out
    assert "## Meta-Style" in out


def test_render_treats_blank_philosophy_as_none(monkeypatch):
    monkeypatch.setattr(renderer, "ask", _fake_ask)
    per_lang = {"python": {"loc": 2000, "repos": 2, "top_rules": ["- rule a"]}}
    out = renderer.render(per_lang, philosophy="   \n\n  ")
    assert "How I think" not in out
