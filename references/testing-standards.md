# Testing Standards Reference

## Test Types and When to Use Each

### Unit Tests
- **What**: Test individual functions/methods in isolation
- **When**: Business logic, utility functions, data transformations, validators
- **Coverage target**: 80%+ for business-critical code
- **Tools**: Jest, Vitest, pytest, go test, PHPUnit, RSpec

### Integration Tests
- **What**: Test multiple components working together
- **When**: API endpoints, database operations, service interactions
- **Coverage target**: All CRUD operations, all API routes
- **Tools**: Supertest, pytest + httpx, testcontainers

### E2E Tests
- **What**: Test full user flows through the real UI
- **When**: Critical user journeys (signup, checkout, core features)
- **Coverage target**: Top 5-10 user flows
- **Tools**: Playwright, Cypress, Selenium

## What MUST Be Tested

### Always Test (Critical Paths)
- Authentication flows (login, signup, password reset, logout)
- Payment processing (charges, refunds, webhooks)
- Data mutations (create, update, delete)
- Authorization checks (who can access what)
- Input validation and sanitization
- Error handling and edge cases

### Should Test
- API response shapes and status codes
- Database queries return expected results
- External service integration points (with mocks)
- State management logic
- Form validation rules
- Pagination and filtering

### Nice to Test
- UI component rendering
- CSS class application
- Loading and error states
- Accessibility (aria attributes, keyboard nav)

## Test Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|-------------|-------------|----------------|
| Snapshot tests for everything | Tests implementation, not behavior | Assert specific values |
| Testing implementation details | Breaks on refactor | Test inputs → outputs |
| Heavy mocking | Tests become fiction | Use real deps or testcontainers |
| `sleep()` in tests | Slow and flaky | Use `waitFor()` / polling |
| No assertions | Test always passes | Add `expect()` calls |
| Shared mutable state | Tests affect each other | Isolate test data |
| Testing third-party code | Not your responsibility | Test your integration layer |
| Skipped tests forever | Rot and lose context | Fix or delete |

## Test Structure (AAA Pattern)

```
Arrange  — Set up test data and dependencies
Act      — Execute the function/action being tested
Assert   — Verify the result matches expectations
```

## Test Naming

```
test("[unit] - [action] - [expected result]")
test("createUser - with valid email - returns user object")
test("createUser - with duplicate email - throws ConflictError")
test("deletePost - when not author - returns 403")
```

## Database Testing

- Use a separate test database
- Reset state between tests (transactions or truncation)
- Use factories/fixtures for test data (not hardcoded)
- Test with realistic data shapes
- Test constraints (unique, not null, foreign keys)

## API Testing Checklist

For every API endpoint, test:
- [ ] Happy path returns correct status and shape
- [ ] Invalid input returns 400 with error message
- [ ] Unauthorized access returns 401
- [ ] Forbidden access returns 403
- [ ] Not found returns 404
- [ ] Server error is handled gracefully (500)
- [ ] Rate limiting works
- [ ] Pagination works with edge cases (empty, single, full)

## CI Integration

- Run unit tests on every push
- Run integration tests on every PR
- Run E2E tests on merge to main
- Fail the build on test failure (never skip)
- Track coverage trends (don't allow regression)
