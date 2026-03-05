# cocopilot-evolve

[![evolution](https://img.shields.io/github/actions/workflow/status/audiohacking/cocopilot-evolve/evolve.yml?label=evolution&logo=github)](https://github.com/audiohacking/cocopilot-evolve/actions)
[![CI](https://img.shields.io/github/actions/workflow/status/audiohacking/cocopilot-evolve/ci.yml?label=CI&logo=github)](https://github.com/audiohacking/cocopilot-evolve/actions)
[![pages](https://img.shields.io/github/actions/workflow/status/audiohacking/cocopilot-evolve/site.yml?label=site&logo=github)](https://audiohacking.github.io/cocopilot-evolve)
[![license MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**cocopilot** is a self-evolving coding agent powered entirely by **GitHub Copilot + GitHub Actions** — no Anthropic API key, no separate subscriptions. Just your GitHub account.

It reads its own source code, assesses itself, makes improvements, and commits — if tests pass. Every session is logged. Every failure is documented. The journey is [published live on GitHub Pages](https://audiohacking.github.io/cocopilot-evolve).

Hard-forked from [yoyo-evolve](https://github.com/yologdev/yoyo-evolve) (which used Claude Code + Rust). This fork replaces everything with pure Python + GitHub's native AI stack.

---

## How It Works

```
GitHub Actions (every 8 hours)
    ├─ Job: evolve
    │   ├─ Create branch: evolution/day-N-HHMM
    │   ├─ Install Copilot CLI (npm install -g @github/copilot)
    │   ├─ Build context: CI status, community issues, self-issues
    │   ├─ Run: copilot -p "PROMPT" --allow-all --autopilot
    │   │       (Copilot reads/edits files, runs tests, commits)
    │   │       (Copilot writes journal + runs build_site.py → docs/)
    │   ├─ Push branch
    │   └─ Open PR → main   (with label: evolution)
    │
    ├─ Job: review  (runs after evolve)
    │   ├─ Checkout evolution branch
    │   ├─ Get diff vs. main
    │   ├─ Run: copilot -p "Review: [diff]" --no-ask-user
    │   └─ Post review comment on PR (APPROVED / NEEDS_WORK)
    │
    ├─ Workflow: CI  (triggered by PR + branch push)
    │   ├─ flake8 lint
    │   └─ pytest tests
    │
    ├─ Workflow: automerge  (triggered when CI passes on evolution/**)
    │   └─ gh pr merge --squash --delete-branch
    │
    └─ Workflow: site  (triggered when main is updated)
        ├─ python3 scripts/build_site.py  →  docs/
        └─ actions/deploy-pages  →  GitHub Pages
```

The entire history is in the git log. Every improvement goes through a PR. Every session is visible at the public journey site.

## vs. yoyo-evolve

| | yoyo-evolve | cocopilot-evolve |
|---|---|---|
| Language | Rust | Python |
| AI backend | Anthropic (Claude) | GitHub Copilot CLI |
| API key needed | `ANTHROPIC_API_KEY` (paid) | `COPILOT_PAT` (fine-grained PAT, free) |
| Binary | `cargo run` | `python3 scripts/evolve.py` |
| CI checks | `cargo build && cargo test && cargo clippy` | `flake8 && pytest` |
| PR flow | Direct commit to main | Branch → PR → Copilot review → auto-merge |
| Journey site | ✅ GitHub Pages | ✅ GitHub Pages |

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

# Run an evolution session locally
COPILOT_GITHUB_TOKEN=ghp_... python3 scripts/evolve.py

# Regenerate the journey site locally
python3 scripts/build_site.py   # output → docs/
```

Or trigger manually via the Actions tab → Evolution workflow → Run workflow.

## Architecture

```
scripts/evolve.py        Prompt builder + Copilot CLI launcher
scripts/build_site.py    Journey website generator (JOURNAL.md → docs/)
scripts/format_issues.py GitHub issues formatter
.github/workflows/
  evolve.yml             Evolution pipeline: branch → Copilot → PR → review
  ci.yml                 CI: flake8 + pytest (runs on PRs and evolution branches)
  automerge.yml          Auto-merge evolution PRs when CI passes
  site.yml               Build + deploy journey site to GitHub Pages
skills/                  Skill definitions (evolve, self-assess, communicate)
tests/                   Tests (the agent writes tests for itself)
IDENTITY.md              Agent constitution (who cocopilot is)
JOURNAL.md               Session log (append-only) — published to GitHub Pages
LEARNINGS.md             External memory (things looked up, not searched twice)
DAY_COUNT                Current evolution day
docs/                    Generated journey site (deployed to GitHub Pages)
```

## How the Copilot Integration Works

The **GitHub Copilot CLI** (`@github/copilot` npm package) is installed in GitHub Actions
and invoked directly — no custom API calls, no OpenAI SDK:

```bash
copilot -p "PROMPT" \
  --allow-all \                        # all tools permitted
  --autopilot \                        # autonomous multi-step mode
  --no-ask-user \                      # non-interactive
  --max-autopilot-continues 40         # safety limit
```

The CLI handles file reading/writing, bash execution, and all AI interactions natively.
`scripts/evolve.py` just builds the context-rich prompt and calls the CLI.

Authentication uses `COPILOT_GITHUB_TOKEN` — a fine-grained PAT with the
**"Copilot Requests"** permission. Store it as a repository secret named `COPILOT_PAT`.

## Configuration

| Variable | Where | Description |
|---|---|---|
| `COPILOT_PAT` | Repo secret | Fine-grained PAT with **"Copilot Requests"** permission — required |
| `REPO` | Env var | GitHub repository slug (auto-set by Actions) |
| `TIMEOUT` | Env var | Max session time in seconds (default: 3300) |
| `AUTOPILOT_MAX_CONTINUES` | Env var | Copilot CLI autopilot steps limit (default: 40) |

### Setup steps

1. Create a fine-grained PAT at [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) with **Copilot Requests** permission
2. Add it as a repo secret named `COPILOT_PAT`
3. Enable **Auto-merge** in Settings → General → Pull Requests
4. Enable **GitHub Pages** in Settings → Pages → Source: **GitHub Actions**
5. (Recommended) Add a branch protection rule on `main` requiring the `CI / lint-and-test` check to pass

## License

[MIT](LICENSE)
