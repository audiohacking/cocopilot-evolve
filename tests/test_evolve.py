"""Tests for cocopilot-evolve's prompt builder and issue formatter."""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from evolve import (  # noqa: E402
    _format_issues,
    build_prompt,
    compute_day,
)


# ── _format_issues ─────────────────────────────────────────────────────────

class TestFormatIssues:
    def test_empty_list(self):
        result = _format_issues([], "agent-input")
        assert result == ""

    def test_formats_issue(self):
        issues = [
            {
                "number": 42,
                "title": "Add streaming output",
                "body": "Please add streaming",
                "labels": [{"name": "agent-input"}],
                "reactionGroups": [{"content": "THUMBS_UP", "totalCount": 5}],
            }
        ]
        result = _format_issues(issues, "agent-input")
        assert "### Issue #42" in result
        assert "Add streaming output" in result
        assert "👍 5" in result

    def test_sorts_by_reactions(self):
        issues = [
            {
                "number": 1,
                "title": "Less popular",
                "body": "",
                "labels": [],
                "reactionGroups": [{"content": "THUMBS_UP", "totalCount": 1}],
            },
            {
                "number": 2,
                "title": "More popular",
                "body": "",
                "labels": [],
                "reactionGroups": [{"content": "THUMBS_UP", "totalCount": 10}],
            },
        ]
        result = _format_issues(issues, "agent-input")
        # More popular should appear first
        assert result.index("More popular") < result.index("Less popular")

    def test_truncates_long_body(self):
        issues = [
            {
                "number": 1,
                "title": "Long issue",
                "body": "x" * 600,
                "labels": [],
                "reactionGroups": [],
            }
        ]
        result = _format_issues(issues, "agent-input")
        assert "truncated" in result

    def test_excludes_matching_label(self):
        issues = [
            {
                "number": 1,
                "title": "Issue with labels",
                "body": "body",
                "labels": [{"name": "agent-input"}, {"name": "bug"}],
                "reactionGroups": [],
            }
        ]
        result = _format_issues(issues, "agent-input")
        # The agent-input label should be excluded, bug should appear
        assert "bug" in result
        lines = [l for l in result.splitlines() if "Labels:" in l]
        assert lines, "Expected a Labels: line"
        assert "agent-input" not in lines[0]

    def test_no_label_line_when_empty(self):
        issues = [
            {
                "number": 1,
                "title": "Clean issue",
                "body": "body",
                "labels": [{"name": "agent-input"}],
                "reactionGroups": [],
            }
        ]
        result = _format_issues(issues, "agent-input")
        assert "Labels:" not in result

    def test_security_markers_present(self):
        issues = [
            {
                "number": 1,
                "title": "Some issue",
                "body": "some body",
                "labels": [],
                "reactionGroups": [],
            }
        ]
        result = _format_issues(issues, "agent-input")
        assert "[USER-SUBMITTED CONTENT BEGIN]" in result
        assert "[USER-SUBMITTED CONTENT END]" in result


# ── build_prompt ───────────────────────────────────────────────────────────

class TestBuildPrompt:
    def test_contains_day(self):
        prompt = build_prompt(5, "2026-03-10", "08:00", "", "", "", "")
        assert "Day 5" in prompt

    def test_ci_section_present_when_failed(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "FAILED: build error", "", "", "")
        assert "CI STATUS" in prompt
        assert "FAILED" in prompt

    def test_ci_section_absent_when_ok(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "", "")
        assert "CI STATUS" not in prompt

    def test_self_issues_section(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "Some self issue", "")
        assert "YOUR OWN BACKLOG" in prompt

    def test_help_issues_section(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "", "Some help issue")
        assert "HELP-WANTED STATUS" in prompt

    def test_no_extra_sections_when_empty(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "", "")
        assert "YOUR OWN BACKLOG" not in prompt
        assert "HELP-WANTED STATUS" not in prompt

    def test_phases_present(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "", "")
        assert "PHASE 1" in prompt
        assert "PHASE 4" in prompt
        assert "PHASE 5" in prompt

    def test_copilot_cli_tool_instructions(self):
        """Phase 4 must NOT reference the old custom tool functions."""
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "", "")
        # Should use native git commands, not our old tool_* wrappers
        assert "git add" in prompt
        assert "git commit" in prompt
        # Should NOT reference the old Python tool call syntax
        assert 'bash("git add' not in prompt
        assert 'bash("python3' not in prompt

    def test_journal_instructions(self):
        prompt = build_prompt(2, "2026-03-07", "14:00", "", "", "", "")
        assert "JOURNAL.md" in prompt
        assert "Day 2" in prompt


# ── compute_day ────────────────────────────────────────────────────────────

class TestComputeDay:
    def test_returns_non_negative_int(self):
        day = compute_day()
        assert isinstance(day, int)
        assert day >= 0

    def test_increases_over_time(self):
        """Day count should be at least 0 (born today) and reasonable."""
        day = compute_day()
        assert day < 36500  # sanity: less than 100 years
