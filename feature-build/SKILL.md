---
name: feature-build
description: Wrapper skill for Claude Code. Use when the user wants to build a new feature from scratch. Automatically runs the Detection Layer first, generates a plan and tasks, implements with quality gates, then generates a report. Delegate to the shared codeguard package.
---

# Feature Build Wrapper

This is a Claude-facing wrapper so `/feature-build` appears as a direct command.

Use the shared package here:

- `~/.claude/skills/codeguard/SKILL.md`
- `~/.claude/skills/codeguard/subskills/feature-build/SKILL.md`

## Required Flow

1. Read the root codeguard skill.
2. Read the `feature-build` subskill.
3. Run the Detection Layer BEFORE any implementation.
4. Generate PLAN.md and TASKS.md.
5. Implement only after plan approval.
6. Run verification after implementation.
7. Generate REPORT.md.
