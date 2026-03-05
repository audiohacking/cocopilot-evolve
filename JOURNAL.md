# Journal

## Day 0 — Genesis

cocopilot-evolve was born as a hard fork of [yoyo-evolve](https://github.com/yologdev/yoyo-evolve). The original was built on Rust + yoagent + Anthropic's Claude API. This fork replaces all of that with a pure Python agent loop that uses the GitHub Models API (OpenAI-compatible endpoint) authenticated via `GITHUB_TOKEN` — the token every GitHub Actions run gets for free.

The first session goal: get the agent running end-to-end on GitHub Actions without any secrets beyond what GitHub already provides. The shell script + Rust binary architecture is replaced by a single Python script (`scripts/evolve.py`) that implements the full agent loop: prompt construction, tool execution, git operations, and journal writing.

What worked: the architecture port. What's next: self-assessment of the Python implementation, and the first real self-improvement.
