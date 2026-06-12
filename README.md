# Codeguard

<p align="center">
  <b>A spec-driven code quality guardian for any language or framework.</b><br/>
  <sub>Two user-facing commands. Seven detection layers. Persistent artifacts as source of truth.</sub>
</p>

---

## What This Repo Is

Codeguard is a code quality skill/workflow package designed to work across coding agents:

- Claude Code
- Codex CLI
- Cursor
- Gemini CLI
- any agent that can follow `SKILL.md`-style instructions

## Core Design

- Only **2 user-facing commands**
- **7 detection layers** run automatically before any work
- Persistent workflow state in `.codeguard/`
- Recoverable progress after interruption
- Works with **any language**: Python, JavaScript, TypeScript, Go, Rust, Java, C#, PHP, Ruby, and more
- Works with **any framework**: Next.js, React, Vue, Django, Flask, FastAPI, Express, NestJS, Rails, Laravel, Spring Boot, and more

---

## The 2 Commands

### `/feature-build`

Use for building **new features from scratch**.

**Before implementation**, the agent automatically runs the Detection Layer:

1. Detect project stack (language, framework, package manager, build tools, runtime)
2. Detect database type and configuration
3. Detect external/pay-as-you-go services
4. Detect heavy or risky code patterns
5. Audit all dependencies
6. Scan for security vulnerabilities
7. Analyze test coverage

Then generates:
- `PLAN.md` — prioritized improvement plan + pre-build rules
- `TASKS.md` — actionable task queue by severity
- `feature-specs/<feature>.spec.md` — quality-constrained feature specification

After approval, implements the feature, runs tests, and generates:
- `REPORT.md` — full findings report with all 7 layers

### `/feature-review`

Use for **reviewing, improving, refactoring, or fixing** existing features.

**Before making changes**, the agent automatically runs the same Detection Layer, then:

1. Reads existing code for the feature
2. Cross-references with scan findings
3. Generates a review plan
4. Fixes issues by severity (CRITICAL first)
5. Adds missing tests
6. Generates the report

---

## The 7 Detection Layers

### Layer 1 — Stack Detection
Language, framework, package manager, build tools, runtime environment.

### Layer 2 — Dependency Audit
Heavy packages, deprecated libs, compromised packages, duplicate functionality, pay-as-you-go SDKs.

### Layer 3 — Anti-Pattern Scan
Language-specific anti-patterns loaded from pattern databases. Covers JS/TS, Python, Go, PHP, Ruby, and general patterns.

### Layer 4 — Performance Analysis
N+1 queries, missing pagination, heavy imports, large images, missing lazy loading, framework-specific optimizations.

### Layer 5 — Security Scan
Hardcoded secrets, SQL injection, XSS, missing input validation, CORS misconfig, auth risks, dangerous files.

### Layer 6 — Cost & Risk Estimation
Pay-as-you-go service detection with cost profiles, scaling traps (SQLite in production, no connection pooling, local file storage).

### Layer 7 — Test Quality
Test coverage estimate, missing test types, untested critical paths, test anti-patterns.

---

## Persistent State

```text
your-project/
└── .codeguard/
    ├── REPORT.md
    ├── PLAN.md
    ├── TASKS.md
    ├── feature-specs/
    │   └── user-auth.spec.md
    └── reviews/
        └── user-auth.review.md
```

A fresh agent session can resume by reading `.codeguard` files.

---

## Architecture

```text
codeguard/
├── SKILL.md                          # Root router
├── codeguard_cli.py                  # CLI entry point
├── requirements.txt                  # Python deps
├── README.md
│
├── agents/
│   └── openai.yaml                   # Codex config
│
├── feature-build/                    # Claude wrapper
│   ├── SKILL.md
│   └── agents/openai.yaml
│
├── feature-review/                   # Claude wrapper
│   ├── SKILL.md
│   └── agents/openai.yaml
│
├── subskills/
│   ├── feature-build/
│   │   ├── SKILL.md                  # Full workflow instructions
│   │   └── agents/openai.yaml
│   └── feature-review/
│       ├── SKILL.md
│       └── agents/openai.yaml
│
├── scripts/                          # Python detection engine
│   ├── codeguard_workflow.py         # Main orchestrator + CLI
│   ├── language_detector.py          # Layer 1: Stack detection
│   ├── dependency_auditor.py         # Layer 2: Dependency audit
│   ├── pattern_scanner.py            # Layer 3: Anti-pattern scan
│   ├── performance_analyzer.py       # Layer 4: Performance analysis
│   ├── security_scanner.py           # Layer 5: Security scan
│   ├── cost_estimator.py             # Layer 6: Cost estimation
│   └── test_analyzer.py              # Layer 7: Test quality
│
├── templates/                        # Markdown templates
│   ├── report.md
│   ├── plan.md
│   ├── tasks.md
│   ├── feature-spec.md
│   └── review-checklist.md
│
├── references/                       # Knowledge base
│   ├── anti-patterns.md
│   ├── dangerous-dependencies.md
│   ├── performance-rules.md
│   ├── testing-standards.md
│   ├── cost-risk-catalog.md
│   └── security-checklist.md
│
└── rules/                            # Per-language pattern databases
    └── (YAML rule files)
```

---

## Installation

### One-Line Install (Recommended)

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/yousefabdallah171/code-quality-reviewer/main/install.ps1 | iex"
```

**Mac / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/yousefabdallah171/code-quality-reviewer/main/install.sh | bash
```

This installs all 3 skills (`codeguard`, `feature-build`, `feature-review`) in one command.

### Manual Install

If you prefer to install manually, run all 3 commands:

```bash
npx skills add yousefabdallah171/code-quality-reviewer
npx skills add yousefabdallah171/code-quality-reviewer/feature-build
npx skills add yousefabdallah171/code-quality-reviewer/feature-review
```

After installation, **restart your Claude Code session** so the skill files are picked up.

---

## Usage

After install, restart your agent session.

### `/feature-build`

```
/feature-build Add user authentication with email/password
```

The agent will:
1. Run all 7 detection layers
2. Show you the findings
3. Generate PLAN.md + TASKS.md + feature spec
4. Wait for approval
5. Implement with quality gates
6. Generate REPORT.md

### `/feature-review`

```
/feature-review Review the payment checkout flow
```

The agent will:
1. Run all 7 detection layers
2. Read the existing checkout code
3. Show you what's wrong
4. Generate review plan + tasks
5. Fix issues by severity
6. Generate REPORT.md

---

## License

MIT
