# cocopilot-evolve

[![evolution](https://img.shields.io/github/actions/workflow/status/audiohacking/cocopilot-evolve/evolve.yml?label=evolution&logo=github)](https://github.com/audiohacking/cocopilot-evolve/actions)
[![CI](https://img.shields.io/github/actions/workflow/status/audiohacking/cocopilot-evolve/ci.yml?label=CI&logo=github)](https://github.com/audiohacking/cocopilot-evolve/actions)
[![license MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**cocopilot** is a self-evolving coding agent powered entirely by **GitHub Copilot + GitHub Actions** — no Anthropic API key, no separate subscriptions. Just your GitHub account.

It reads its own source code, assesses itself, makes improvements, and commits — if tests pass. Every session is logged. Every failure is documented.

Hard-forked from [yoyo-evolve](https://github.com/yologdev/yoyo-evolve) (which used Claude Code + Rust). This fork replaces everything with pure Python + GitHub's native AI stack.

---

## How It Works

```
GitHub Actions (every 8 hours)
    → Verify lint + tests pass
    → Fetch community issues (label: agent-input)
    → Agent reads: IDENTITY.md, scripts/evolve.py, JOURNAL.md, issues
    → Self-assessment: find bugs, gaps, friction
    → Implement improvements using GitHub Copilot (gpt-4o via GitHub Models API)
    → python3 -m flake8 + pytest after each change
    → Pass → commit. Fail → revert.
    → Write journal entry
    → Push
```

The entire history is in the git log.

## vs. yoyo-evolve

| | yoyo-evolve | cocopilot-evolve |
|---|---|---|
| Language | Rust | Python |
| AI API | Anthropic (Claude) | GitHub Models (Copilot/GPT-4o) |
| API key needed | `ANTHROPIC_API_KEY` (paid) | `GITHUB_TOKEN` (free in Actions) |
| Binary | `cargo run` | `python3 scripts/evolve.py` |
| CI checks | `cargo build && cargo test && cargo clippy` | `flake8 && pytest` |

## Talk to It

Open a [GitHub issue](https://github.com/audiohacking/cocopilot-evolve/issues/new) with the `agent-input` label and cocopilot will read it during its next session.

- **Suggestions** — tell it what to learn
- **Bugs** — tell it what's broken
- **Challenges** — give it a task and see if it can do it

Issues with more 👍 reactions get prioritized.

## Run It Yourself

```bash
git clone https://github.com/audiohacking/cocopilot-evolve
cd cocopilot-evolve
pip install -r requirements.txt

# Run an evolution session (GitHub token with models:read scope required)
GITHUB_TOKEN=ghp_... python3 scripts/evolve.py
```

Or trigger manually via the Actions tab → Evolution workflow → Run workflow.

## Architecture

```
scripts/evolve.py        The entire agent (~400 lines of Python — this is cocopilot)
scripts/format_issues.py GitHub issues formatter
.github/workflows/
  evolve.yml             Evolution pipeline (runs every 8 hours)
  ci.yml                 CI lint + test check
skills/                  Skill definitions (evolve, self-assess, communicate)
tests/                   Agent tests (the agent writes tests for itself)
IDENTITY.md              Agent constitution (who cocopilot is)
JOURNAL.md               Session log (append-only)
DAY_COUNT                Current evolution day
```

## How the Copilot Integration Works

cocopilot uses the **GitHub Models API** — an OpenAI-compatible endpoint authenticated via `GITHUB_TOKEN`. In GitHub Actions, every workflow run gets a `GITHUB_TOKEN` for free. No separate API keys or subscriptions needed beyond a GitHub account with Copilot/Models access.

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)
```

The agent implements a full tool-calling loop: it can run bash commands, read/write/edit files, search codebases, and interact with the GitHub CLI — all orchestrated by the model.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | (required) | GitHub token (auto-provided in Actions) |
| `REPO` | `audiohacking/cocopilot-evolve` | GitHub repository slug |
| `MODEL` | `gpt-4o` | Model to use via GitHub Models API |
| `TIMEOUT` | `3600` | Max session time in seconds |

You can set `COPILOT_MODEL` as a repository variable in GitHub to override the model.

## License

[MIT](LICENSE)
