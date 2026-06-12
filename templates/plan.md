# Codeguard Plan — {{PROJECT_NAME}}

## Current State

- Primary Language:
- Frameworks:
- Security Critical Issues: 0
- Cost Risk Level: LOW
- Test Coverage: UNKNOWN

## Priority Order

1. Fix all CRITICAL security issues
2. Fix injection vulnerabilities
3. Address cost/scaling traps
4. Add missing tests for critical paths
5. Fix deprecated dependencies
6. Address performance issues
7. Clean up code quality warnings

## Pre-Build Rules

Before building ANY new feature:

1. Read PLAN.md and REPORT.md
2. Check if the feature area has known issues
3. Generate a feature spec
4. Include quality constraints from the report
5. Write tests alongside implementation
6. Re-scan after implementation

## Quality Gates

- [ ] No new critical findings
- [ ] Input validation on all endpoints
- [ ] Parameterized database queries
- [ ] New dependencies justified
- [ ] Tests written and passing
- [ ] Cost implications documented
