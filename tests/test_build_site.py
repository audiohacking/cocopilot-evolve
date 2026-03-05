"""Tests for scripts/build_site.py — journey website generator."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_site import parse_journal, parse_identity, render_journal, render_identity  # noqa: E402


# ── parse_journal ──────────────────────────────────────────────────────────

class TestParseJournal:
    def test_empty_content(self):
        assert parse_journal("") == []

    def test_no_day_entries(self):
        assert parse_journal("# Journal\n\nNo entries yet.\n") == []

    def test_single_entry(self):
        content = "# Journal\n\n## Day 0 — Genesis\n\nFirst session.\n"
        entries = parse_journal(content)
        assert len(entries) == 1
        assert entries[0]["day"] == 0
        assert "Genesis" in entries[0]["title"]
        assert "First session" in entries[0]["body"]

    def test_multiple_entries(self):
        content = (
            "## Day 5 — Fifth session\n\nDid stuff.\n\n"
            "## Day 1 — First session\n\nStarted.\n"
        )
        entries = parse_journal(content)
        assert len(entries) == 2
        assert entries[0]["day"] == 5
        assert entries[1]["day"] == 1

    def test_em_dash_separator(self):
        content = "## Day 3 — Title with em dash\n\nBody.\n"
        entries = parse_journal(content)
        assert entries[0]["day"] == 3
        assert "Title with em dash" in entries[0]["title"]

    def test_hyphen_separator(self):
        content = "## Day 2 - Hyphen title\n\nBody.\n"
        entries = parse_journal(content)
        assert entries[0]["day"] == 2

    def test_entry_body_stripped(self):
        content = "## Day 1 — Title\n\n  body with spaces  \n"
        entries = parse_journal(content)
        assert entries[0]["body"] == "body with spaces"


# ── parse_identity ─────────────────────────────────────────────────────────

class TestParseIdentity:
    def test_empty_content(self):
        result = parse_identity("")
        assert result == {"intro": [], "rules": []}

    def test_rules_extracted(self):
        content = (
            "# Who I Am\n\nI am cocopilot.\n\n"
            "## My Rules\n\n"
            "1. **First rule** be careful\n"
            "2. **Second rule** be precise\n"
        )
        result = parse_identity(content)
        assert len(result["rules"]) == 2
        assert "First rule" in result["rules"][0]
        assert "Second rule" in result["rules"][1]

    def test_intro_extracted(self):
        content = "# Who I Am\n\nI am a self-evolving agent.\n"
        result = parse_identity(content)
        assert any("self-evolving" in line for line in result["intro"])


# ── render_journal ─────────────────────────────────────────────────────────

class TestRenderJournal:
    def test_empty_entries(self):
        html = render_journal([])
        assert "timeline-empty" in html
        assert "No journal entries" in html

    def test_single_entry_rendered(self):
        entries = [{"day": 1, "title": "First day", "body": "Hello world."}]
        html = render_journal(entries)
        assert "Day 1" in html
        assert "First day" in html
        assert "Hello world" in html

    def test_entry_html_escaping(self):
        entries = [{"day": 1, "title": "<script>bad</script>", "body": ""}]
        html = render_journal(entries)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_multiple_entries(self):
        entries = [
            {"day": 2, "title": "Second", "body": ""},
            {"day": 1, "title": "First", "body": ""},
        ]
        html = render_journal(entries)
        assert html.index("Day 2") < html.index("Day 1")


# ── render_identity ────────────────────────────────────────────────────────

class TestRenderIdentity:
    def test_empty_identity(self):
        html = render_identity({"intro": [], "rules": []})
        assert html == ""

    def test_mission_rendered(self):
        html = render_identity({"intro": ["I am the agent."], "rules": []})
        assert 'class="mission"' in html
        assert "I am the agent" in html

    def test_rules_rendered(self):
        html = render_identity({"intro": [], "rules": ["<strong>Rule one</strong>"]})
        assert 'class="rules"' in html
        assert "Rule one" in html

    def test_html_escaping_in_identity(self):
        html = render_identity({"intro": ["<evil>"], "rules": []})
        assert "<evil>" not in html
        assert "&lt;evil&gt;" in html


# ── build() integration ────────────────────────────────────────────────────

class TestBuild:
    def test_build_creates_files(self, tmp_path, monkeypatch):
        """build() should write index.html and style.css into docs/."""
        import build_site as bs

        # Point ROOT at tmp_path so we read/write there
        monkeypatch.setattr(bs, "ROOT", tmp_path)
        monkeypatch.setattr(bs, "DOCS", tmp_path / "docs")

        (tmp_path / "JOURNAL.md").write_text(
            "## Day 0 — Genesis\n\nFirst session.\n"
        )
        (tmp_path / "IDENTITY.md").write_text(
            "# Who I Am\n\nI am cocopilot.\n\n## My Rules\n\n1. **Be honest**\n"
        )
        (tmp_path / "DAY_COUNT").write_text("0\n")

        bs.build()

        assert (tmp_path / "docs" / "index.html").exists()
        assert (tmp_path / "docs" / "style.css").exists()

    def test_build_content_reflects_journal(self, tmp_path, monkeypatch):
        """Generated HTML should contain journal entry content."""
        import build_site as bs

        monkeypatch.setattr(bs, "ROOT", tmp_path)
        monkeypatch.setattr(bs, "DOCS", tmp_path / "docs")

        (tmp_path / "JOURNAL.md").write_text(
            "## Day 3 — Great progress\n\nFixed everything.\n"
        )
        (tmp_path / "IDENTITY.md").write_text("")
        (tmp_path / "DAY_COUNT").write_text("3\n")

        bs.build()

        html = (tmp_path / "docs" / "index.html").read_text()
        assert "Day 3" in html
        assert "Great progress" in html
        assert "Fixed everything" in html

    def test_build_missing_files_graceful(self, tmp_path, monkeypatch):
        """build() should not crash when source files are absent."""
        import build_site as bs

        monkeypatch.setattr(bs, "ROOT", tmp_path)
        monkeypatch.setattr(bs, "DOCS", tmp_path / "docs")

        # No JOURNAL.md, IDENTITY.md, or DAY_COUNT
        bs.build()
        assert (tmp_path / "docs" / "index.html").exists()
