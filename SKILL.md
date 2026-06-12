---
name: codeguard
description: Spec-driven code quality guardian for any language or framework. Detects anti-patterns, dangerous dependencies, performance risks, security holes, cost traps, and missing tests. Generates persistent .codeguard artifacts so any agent session can resume. Two commands — feature-build for building new features with quality gates, feature-review for reviewing and improving existing features.
---

# Codeguard

Use this skill as the root router for a language-agnostic code quality workflow.

## Public Workflow Surface

Expose only two primary workflows:

- `feature-build`
- `feature-review`

Do not present internal helpers, detectors, or scanners as primary user-facing workflows.

## Source Of Truth

Always read and update these project artifacts first:

- `.codeguard/REPORT.md`
- `.codeguard/PLAN.md`
- `.codeguard/TASKS.md`
- `.codeguard/feature-specs/*.spec.md`
- `.codeguard/reviews/*.review.md`

Never rely on chat history as the workflow memory.

## Workflow Routing

For building a new feature from scratch:

- read `subskills/feature-build/SKILL.md`

For reviewing, improving, refactoring, or fixing an existing feature:

- read `subskills/feature-review/SKILL.md`

## Internal Helpers

Use internal scripts for detection and analysis:

- `scripts/codeguard_workflow.py` — main orchestrator
- `scripts/language_detector.py` — detect language, framework, toolchain
- `scripts/dependency_auditor.py` — audit deps for risk, cost, weight, deprecation
- `scripts/pattern_scanner.py` — scan for anti-patterns per language
- `scripts/performance_analyzer.py` — find N+1 queries, missing pagination, heavy imports
- `scripts/security_scanner.py` — find hardcoded secrets, injection patterns, misconfigs
- `scripts/cost_estimator.py` — detect pay-as-you-go services, unbounded calls, scaling traps
- `scripts/test_analyzer.py` — evaluate test coverage, quality, and missing tests

Use references as domain knowledge:

- `references/anti-patterns.md`
- `references/dangerous-dependencies.md`
- `references/performance-rules.md`
- `references/testing-standards.md`
- `references/cost-risk-catalog.md`
- `references/security-checklist.md`

## Non-Negotiables

1. Persist all findings into `.codeguard/` artifacts.
2. Detect language and framework before running any analysis.
3. Load only the rules relevant to the detected stack.
4. Always check for dangerous dependencies, cost traps, and security holes.
5. Generate actionable tasks, not vague warnings.
6. Every finding must have a severity (critical, warning, info) and a fix suggestion.
7. Read current code before generating recommendations.
8. Keep helper commands internal; the visible experience is `feature-build` and `feature-review`.
9. Let the Python scripts do the heavy detection work before asking any questions.
10. Update `.codeguard/TASKS.md` so a fresh agent can resume safely.
11. Before building any feature, the agent MUST read `.codeguard/REPORT.md` to understand known risks.
12. Every feature spec must include a quality checklist derived from the scan findings.
