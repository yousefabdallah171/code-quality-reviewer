---
name: feature-review
description: Wrapper skill for Claude Code. Use when the user wants to review, improve, refactor, or fix an existing feature. Automatically runs the Detection Layer first, generates a review plan and tasks, fixes issues, adds tests, then generates a report. Delegate to the shared codeguard package.
---

# Feature Review Wrapper

This is a Claude-facing wrapper so `/feature-review` appears as a direct command.

Use the shared package here:

- `~/.claude/skills/codeguard/SKILL.md`
- `~/.claude/skills/codeguard/subskills/feature-review/SKILL.md`

## Required Flow

1. Read the root codeguard skill.
2. Read the `feature-review` subskill.
3. Run the Detection Layer BEFORE any changes.
4. Generate REVIEW_PLAN.md and TASKS.md.
5. Fix issues by severity order.
6. Run verification after changes.
7. Generate REPORT.md.
