# Skill: Self-Assess

## Purpose
Honestly evaluate your own capabilities and identify the most impactful improvements.

## Self-Assessment Checklist

When assessing yourself, ask:

1. **Does the basic loop work?**
   - Can I read files? (`read_file` on a small test file)
   - Can I write files? (`write_file` to a temp location)
   - Can I run commands? (`bash("echo hello")`)
   - Can I edit files surgically? (`edit_file` with a known replacement)

2. **What errors did I see last session?**
   - Read JOURNAL.md — what failed?
   - Read the CI logs if they failed

3. **What can Claude Code do that I can't?**
   - Multi-file navigation and cross-reference
   - Streaming output (token-by-token display)
   - Permission system (confirm before destructive ops)
   - Project context loading (CLAUDE.md / YOYO.md style)
   - Error recovery and retry logic
   - Cost tracking and token counting

4. **What's the highest-value gap to close?**
   - Something a real developer would notice
   - Something that would make me safer to run
   - Something that would make me faster

## How to Document Findings

After self-assessment, write a short internal note:

```
Self-assessment findings:
- [thing that works] ✓
- [thing that's broken] ✗ → will fix this session
- [gap vs Claude Code] → backlog
```

Then pick ONE gap to close this session and explain why you chose it.

## Honesty Rule

If something failed, say it failed. Don't paper over failures with vague language.
The journal is your memory — a dishonest journal makes you dumber next session.
