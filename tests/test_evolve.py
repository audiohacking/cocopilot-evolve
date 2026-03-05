"""Tests for cocopilot-evolve's tool implementations."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from evolve import (  # noqa: E402
    _format_issues,
    _summarize_args,
    build_prompt,
    compute_day,
    dispatch_tool,
    tool_bash,
    tool_edit_file,
    tool_list_files,
    tool_read_file,
    tool_search_files,
    tool_write_file,
)


# ── Tool: bash ─────────────────────────────────────────────────────────────

class TestToolBash:
    def test_simple_command(self):
        result = tool_bash("echo hello")
        assert "hello" in result

    def test_exit_code_shown_on_failure(self):
        result = tool_bash("exit 1")
        assert "exit code 1" in result

    def test_timeout(self):
        result = tool_bash("sleep 10", timeout=1)
        assert "TIMEOUT" in result

    def test_stderr_captured(self):
        result = tool_bash("echo err >&2")
        assert "err" in result

    def test_empty_output(self):
        result = tool_bash("true")
        assert result == "(no output)"


# ── Tool: read_file ────────────────────────────────────────────────────────

class TestToolReadFile:
    def test_reads_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = tool_read_file(str(f))
        assert result == "hello world"

    def test_missing_file(self):
        result = tool_read_file("/nonexistent/path/file.txt")
        assert "[ERROR]" in result
        assert "not found" in result


# ── Tool: write_file ───────────────────────────────────────────────────────

class TestToolWriteFile:
    def test_creates_file(self, tmp_path):
        path = str(tmp_path / "new.txt")
        result = tool_write_file(path, "content here")
        assert "Written" in result
        assert Path(path).read_text() == "content here"

    def test_overwrites_existing_file(self, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("old content")
        tool_write_file(str(f), "new content")
        assert f.read_text() == "new content"

    def test_creates_parent_directories(self, tmp_path):
        path = str(tmp_path / "a" / "b" / "c.txt")
        result = tool_write_file(path, "deep")
        assert "Written" in result
        assert Path(path).exists()


# ── Tool: edit_file ────────────────────────────────────────────────────────

class TestToolEditFile:
    def test_replaces_string(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\ny = 2\n")
        result = tool_edit_file(str(f), "x = 1", "x = 42")
        assert "Edited" in result
        assert f.read_text() == "x = 42\ny = 2\n"

    def test_string_not_found(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\n")
        result = tool_edit_file(str(f), "z = 99", "z = 0")
        assert "[ERROR]" in result
        assert "not found" in result

    def test_ambiguous_replacement(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\nx = 1\n")
        result = tool_edit_file(str(f), "x = 1", "x = 99")
        assert "[ERROR]" in result
        assert "2 times" in result

    def test_missing_file(self):
        result = tool_edit_file("/nonexistent/file.py", "old", "new")
        assert "[ERROR]" in result


# ── Tool: list_files ───────────────────────────────────────────────────────

class TestToolListFiles:
    def test_lists_directory(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        result = tool_list_files(str(tmp_path))
        assert "a.txt" in result
        assert "b.txt" in result

    def test_recursive_listing(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "deep.txt").write_text("deep")
        result = tool_list_files(str(tmp_path), recursive=True)
        assert "deep.txt" in result

    def test_missing_path(self):
        result = tool_list_files("/nonexistent/dir")
        assert "[ERROR]" in result

    def test_empty_directory(self, tmp_path):
        result = tool_list_files(str(tmp_path))
        assert result == "(empty directory)"


# ── Tool: search_files ─────────────────────────────────────────────────────

class TestToolSearchFiles:
    def test_finds_pattern(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("def hello():\n    pass\n")
        result = tool_search_files("def hello", str(tmp_path))
        assert "def hello" in result

    def test_no_matches(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        result = tool_search_files("zzz_no_match", str(tmp_path))
        assert "no matches" in result

    def test_file_glob_filter(self, tmp_path):
        (tmp_path / "a.py").write_text("FIND_ME = 1\n")
        (tmp_path / "b.txt").write_text("FIND_ME = 2\n")
        result = tool_search_files("FIND_ME", str(tmp_path), file_glob="*.py")
        assert "a.py" in result


# ── dispatch_tool ──────────────────────────────────────────────────────────

class TestDispatchTool:
    def test_unknown_tool(self):
        result = dispatch_tool("nonexistent", {})
        assert "[ERROR]" in result
        assert "Unknown tool" in result

    def test_bash_dispatch(self):
        result = dispatch_tool("bash", {"command": "echo hi"})
        assert "hi" in result


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

    def test_phases_present(self):
        prompt = build_prompt(1, "2026-03-05", "10:00", "", "", "", "")
        assert "PHASE 1" in prompt
        assert "PHASE 4" in prompt
        assert "PHASE 5" in prompt


# ── _summarize_args ────────────────────────────────────────────────────────

class TestSummarizeArgs:
    def test_bash(self):
        result = _summarize_args("bash", {"command": "echo hi"})
        assert "echo hi" in result

    def test_read_file(self):
        result = _summarize_args("read_file", {"path": "/foo/bar.py"})
        assert "bar.py" in result

    def test_write_file(self):
        result = _summarize_args("write_file", {"path": "x.txt", "content": "abc"})
        assert "x.txt" in result
        assert "3 chars" in result

    def test_long_bash_truncated(self):
        long_cmd = "echo " + "x" * 100
        result = _summarize_args("bash", {"command": long_cmd})
        assert "..." in result


# ── compute_day ────────────────────────────────────────────────────────────

class TestComputeDay:
    def test_returns_non_negative_int(self):
        day = compute_day()
        assert isinstance(day, int)
        assert day >= 0
