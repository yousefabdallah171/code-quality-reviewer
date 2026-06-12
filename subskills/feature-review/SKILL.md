---
name: feature-review
description: Review, improve, refactor, or fix an existing feature with automatic quality analysis. Before making changes, the agent runs the full Detection Layer (stack, language, database, services, patterns), generates REVIEW_PLAN.md and TASKS.md, then reviews the implementation, fixes issues, adds missing tests, checks performance, and generates REPORT.md.
---

# Feature Review

Use this workflow to review, improve, refactor, or fix an existing feature.

## Sequence

### Phase 1 — Automatic Detection (runs before any changes)

1. Run the detection layer automatically:

```bash
python scripts/codeguard_workflow.py scan --path "<project>"
```

This detects:
- Project stack (language, framework, package manager, build tools)
- Programming language and all dependencies
- Database type and configuration
- External/pay-as-you-go services in use
- Heavy or risky code patterns in the current codebase
- Test coverage and quality gaps

2. Read the generated `.codeguard/REPORT.md` to understand all existing issues.

### Phase 2 — Review Planning

3. Read the existing code for the feature being reviewed.
4. Cross-reference with REPORT.md findings to identify issues specific to this feature.
5. Generate `.codeguard/feature-specs/<feature>.spec.md` documenting:
   - Current state of the feature
   - Issues found by the scan
   - Improvement priorities
6. Update `.codeguard/PLAN.md` with the review/fix approach.
7. Update `.codeguard/TASKS.md` with specific improvement tasks.
8. Present the review plan to the user:
   - What issues were found
   - What needs fixing (by severity)
   - What tests are missing
   - Performance and security concerns
   - Cost implications

### Phase 3 — Implementation

9. After user approval, apply fixes following these rules:
   - Fix CRITICAL issues first (security, data safety)
   - Fix WARNING issues second (performance, best practices)
   - Add missing tests for critical paths
   - Preserve working behavior — don't break existing functionality
   - Document all changes in the review file

### Phase 4 — Verification

10. After changes:
    - Run the detection layer again
    - Compare findings with the pre-review state
    - Verify no regressions introduced
    - Verify tests pass
    - Update `.codeguard/REPORT.md` with post-review status
    - Update `.codeguard/TASKS.md` marking completed items
    - Generate `.codeguard/reviews/<feature>.review.md` documenting:
      - What was found
      - What was fixed
      - What was tested
      - What remains open

## Review Focus Areas

When reviewing existing code, specifically look for:

### Security
- Hardcoded secrets or API keys
- SQL injection / XSS vulnerabilities
- Missing input validation
- Weak auth patterns
- CORS misconfigurations

### Performance
- N+1 query patterns
- Missing pagination
- Heavy synchronous operations
- Large bundle imports
- Missing caching

### Cost
- Unbounded API calls to pay-as-you-go services
- Missing rate limiting
- Database scaling traps
- Local storage instead of cloud storage

### Testing
- Missing tests for critical paths
- Test anti-patterns
- No error case coverage

### Code Quality
- Language-specific anti-patterns
- Dead code
- Debug leftovers
- Deprecated dependencies
- Duplicate functionality

## Quality Gates

Before marking the review as complete:

- [ ] All critical findings resolved
- [ ] No new critical findings introduced
- [ ] Missing tests added for critical paths
- [ ] Performance improvements verified
- [ ] Security issues patched
- [ ] TASKS.md updated with final status
