---
name: feature-build
description: Build a new feature from scratch with automatic quality gates. Before implementation, the agent runs the full Detection Layer (stack, language, database, services, patterns), generates PLAN.md and TASKS.md, implements the feature with tests and performance checks, then generates REPORT.md. Use when the user wants to build something new.
---

# Feature Build

Use this workflow to build a new feature from scratch with quality gates.

## Sequence

### Phase 1 — Automatic Detection (runs before any code)

1. Run the detection layer automatically:

```bash
python scripts/codeguard_workflow.py scan --path "<project>"
```

This detects:
- Project stack (language, framework, package manager, build tools)
- Programming language and all dependencies
- Database type and configuration
- External/pay-as-you-go services in use
- Heavy or risky code patterns already in the codebase
- Test coverage and quality gaps

2. Read the generated `.codeguard/REPORT.md` to understand all known risks.

### Phase 2 — Planning

3. Generate the feature spec:

```bash
python scripts/codeguard_workflow.py review --path "<project>" --feature "<feature-name>"
```

4. Update `.codeguard/PLAN.md` with the feature implementation approach.
5. Update `.codeguard/TASKS.md` with the implementation task breakdown.
6. Present the plan to the user. Include:
   - What will be built
   - Known risks in the affected area (from REPORT.md)
   - New dependencies needed (with justification)
   - Cost implications
   - Test strategy

### Phase 3 — Implementation

7. After user approval, implement the feature following these rules:
   - Write tests alongside or before implementation
   - Use parameterized queries for all database operations
   - Validate all user input at boundaries
   - Handle errors for all external calls
   - No hardcoded secrets or magic numbers
   - Follow the detected stack's best practices

### Phase 4 — Verification

8. After implementation:
   - Run the detection layer again on changed files
   - Verify no new critical findings
   - Verify tests pass
   - Update `.codeguard/REPORT.md` with post-build status
   - Update `.codeguard/TASKS.md` marking completed items
   - Generate `.codeguard/reviews/<feature>.review.md` documenting what was done

## Quality Gates

Before marking the feature as complete, verify:

- [ ] No new critical security findings
- [ ] All new endpoints have input validation
- [ ] All database queries are parameterized
- [ ] New dependencies are justified and audited
- [ ] Tests written and passing
- [ ] Performance: no N+1 queries, no unbounded operations
- [ ] Cost: service usage documented and rate-limited
- [ ] Accessibility: keyboard nav, screen reader support where applicable

## Interview Policy

Ask the user only when:
- The feature scope is ambiguous
- A dependency choice has tradeoffs worth discussing
- A cost implication needs business approval
- A security decision requires context

Do not ask about things the detection layer already resolved.
