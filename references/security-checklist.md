# Security Checklist Reference

## OWASP Top 10 — Quick Guard

### 1. Injection (SQL, NoSQL, Command, LDAP)
- **Guard**: Parameterized queries everywhere. Never string-concatenate user input into queries.
- **Check**: Search for `execute(`, `query(`, `${}` in SQL strings, `f"SELECT` patterns.

### 2. Broken Authentication
- **Guard**: Hash passwords with bcrypt/argon2. Use session tokens with expiry. Rate limit login.
- **Check**: Plain text password comparison, JWT without expiry, no rate limit on auth endpoints.

### 3. Sensitive Data Exposure
- **Guard**: Encrypt at rest and in transit. Never log sensitive data. Use env vars for secrets.
- **Check**: Hardcoded API keys, secrets in client bundles, .env files not in .gitignore.

### 4. XML External Entities (XXE)
- **Guard**: Disable DTD processing. Use JSON over XML where possible.
- **Check**: XML parsing without safe configuration.

### 5. Broken Access Control
- **Guard**: Check permissions on every endpoint. Default deny. Validate ownership.
- **Check**: Missing auth middleware, direct object reference without ownership check.

### 6. Security Misconfiguration
- **Guard**: Remove default credentials. Disable debug in production. Set security headers.
- **Check**: `DEBUG=true`, `display_errors=On`, default admin passwords, missing CORS config.

### 7. Cross-Site Scripting (XSS)
- **Guard**: Sanitize all user-generated content. Use framework's auto-escaping.
- **Check**: `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `{!! $var !!}` without sanitization.

### 8. Insecure Deserialization
- **Guard**: Never deserialize untrusted data. Validate JSON schema.
- **Check**: `pickle.loads()`, `unserialize()`, `eval()` on user input.

### 9. Using Components with Known Vulnerabilities
- **Guard**: Run `npm audit`, `pip-audit`, `cargo audit` regularly.
- **Check**: Outdated deps with known CVEs.

### 10. Insufficient Logging & Monitoring
- **Guard**: Log auth events, access control failures, input validation failures. Alert on anomalies.
- **Check**: No logging, `console.log` only, no alerting.

## Secret Management

### Never Commit
- API keys, tokens, passwords
- Private keys (.pem, .key)
- .env files with real values
- Database connection strings with credentials
- Service account JSON files

### Always Use
- Environment variables for all secrets
- Secret managers (AWS Secrets Manager, Vault, Doppler)
- `.env.example` with placeholder values (committed)
- `.env` with real values (gitignored)

### Rotation
- Rotate secrets after any suspected exposure
- Rotate API keys every 90 days
- Use short-lived tokens where possible

## HTTP Security Headers

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## Cookie Security

```
Set-Cookie: session=xxx; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400
```

- `Secure`: Only over HTTPS
- `HttpOnly`: Not accessible via JavaScript
- `SameSite=Strict`: No cross-site requests
- `Max-Age`: Always set expiry

## Input Validation

- Validate type, length, format, and range
- Validate on the SERVER, not just client
- Use allowlists over denylists
- Sanitize before storage AND before display
- Reject unexpected fields (strict schemas)
