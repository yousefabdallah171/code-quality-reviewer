"""Security-focused scanning for codeguard."""

from __future__ import annotations

import re
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".next", "dist", ".git", ".pnpm", "__pycache__",
    ".turbo", "build", "coverage", "target", "vendor", ".venv", "venv",
}

SECRET_PATTERNS = [
    (r"""(?:AKIA[0-9A-Z]{16})""", "AWS Access Key ID"),
    (r"""(?:sk-[a-zA-Z0-9]{20,})""", "OpenAI / Stripe Secret Key"),
    (r"""(?:ghp_[A-Za-z0-9]{36})""", "GitHub Personal Access Token"),
    (r"""(?:gho_[A-Za-z0-9]{36})""", "GitHub OAuth Token"),
    (r"""(?:glpat-[A-Za-z0-9\-]{20,})""", "GitLab Personal Access Token"),
    (r"""(?:xoxb-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{24})""", "Slack Bot Token"),
    (r"""(?:xoxp-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{24})""", "Slack User Token"),
    (r"""(?:SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43})""", "SendGrid API Key"),
    (r"""(?:sq0csp-[A-Za-z0-9_\-]{43})""", "Square Access Token"),
    (r"""(?:AC[a-f0-9]{32})""", "Twilio Account SID"),
    (r"""(?:key-[A-Za-z0-9]{32})""", "Mailgun API Key"),
    (r"""(?:rk_live_[A-Za-z0-9]{24,})""", "Stripe Restricted Key"),
    (r"""(?:pk_live_[A-Za-z0-9]{24,})""", "Stripe Publishable Live Key"),
    (r"""(?:whsec_[A-Za-z0-9]{32,})""", "Stripe Webhook Secret"),
    (r"""(?:-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)""", "Private Key in source"),
]

DANGEROUS_FILE_PATTERNS = [
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "serviceAccountKey.json",
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
]

SECURITY_HEADERS_CHECK = {
    "x-frame-options": "Missing X-Frame-Options. Clickjacking risk.",
    "content-security-policy": "Missing Content-Security-Policy. XSS risk.",
    "strict-transport-security": "Missing HSTS. Downgrade attack risk.",
    "x-content-type-options": "Missing X-Content-Type-Options. MIME sniffing risk.",
}

AUTH_RISK_PATTERNS = {
    "jwt_no_expiry": {
        "pattern": r"""jwt\.sign\([^)]*(?!expiresIn)""",
        "message": "JWT token signed without expiration. Tokens valid forever.",
        "fix": "Add expiresIn: '1h' or similar to jwt.sign() options.",
    },
    "password_plain_compare": {
        "pattern": r"""(?:password\s*===?\s*\w+|if\s*\(\s*\w+\.password\s*===?)""",
        "message": "Possible plain-text password comparison.",
        "fix": "Use bcrypt.compare() or argon2.verify() for password checking.",
    },
    "cors_wildcard": {
        "pattern": r"""(?:origin:\s*['"]?\*['"]?|Access-Control-Allow-Origin.*\*)""",
        "message": "CORS allows all origins. Any website can make requests.",
        "fix": "Restrict to specific domains: origin: 'https://yourdomain.com'",
    },
    "no_rate_limit": {
        "pattern": r"""(?:app\.(?:post|put|patch|delete)\s*\(\s*['"]\/(?:login|auth|signup|register|api))""",
        "message": "Auth/API endpoint without visible rate limiting.",
        "fix": "Add rate limiting with express-rate-limit, bottleneck, or equivalent.",
    },
    "cookie_no_secure": {
        "pattern": r"""(?:cookie|setCookie|set-cookie)(?!.*(?:secure|httpOnly|HttpOnly))""",
        "message": "Cookie set without secure/httpOnly flags.",
        "fix": "Add secure: true, httpOnly: true, sameSite: 'strict' to cookie options.",
    },
}


def scan_for_secrets(root: Path) -> list[dict]:
    findings = []
    source_extensions = {
        ".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".rs", ".java",
        ".cs", ".php", ".rb", ".yaml", ".yml", ".json", ".toml",
        ".env", ".cfg", ".conf", ".ini", ".properties",
    }

    def walk(directory: Path):
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        walk(entry)
                elif entry.is_file():
                    if entry.suffix.lower() in source_extensions or entry.name.startswith(".env"):
                        try:
                            content = entry.read_text(encoding="utf-8", errors="ignore")
                            for pattern, secret_type in SECRET_PATTERNS:
                                for match in re.finditer(pattern, content):
                                    line_num = content[:match.start()].count("\n") + 1
                                    findings.append({
                                        "type": "exposed_secret",
                                        "secret_type": secret_type,
                                        "file": str(entry.relative_to(root)),
                                        "line": line_num,
                                        "severity": "critical",
                                        "message": f"{secret_type} found in source code.",
                                        "fix": "Move to environment variable. Add file to .gitignore. Rotate the key.",
                                        "match_preview": match.group(0)[:8] + "..." + match.group(0)[-4:],
                                    })
                        except (PermissionError, OSError):
                            pass
        except (PermissionError, OSError):
            pass

    walk(root)
    return findings


def scan_for_dangerous_files(root: Path) -> list[dict]:
    findings = []
    for pattern in DANGEROUS_FILE_PATTERNS:
        for f in root.rglob(f"*{pattern}"):
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            gitignore = root / ".gitignore"
            in_gitignore = False
            if gitignore.exists():
                gi_content = gitignore.read_text(encoding="utf-8", errors="ignore")
                if pattern in gi_content or f.name in gi_content:
                    in_gitignore = True
            if not in_gitignore:
                findings.append({
                    "type": "dangerous_file",
                    "file": str(f.relative_to(root)),
                    "severity": "critical",
                    "message": f"Sensitive file '{f.name}' not in .gitignore. May be committed to repo.",
                    "fix": f"Add '{f.name}' to .gitignore immediately. Check git history for exposure.",
                })
    return findings


def scan_auth_risks(root: Path) -> list[dict]:
    findings = []
    source_extensions = {".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".php", ".rb"}

    def walk(directory: Path):
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        walk(entry)
                elif entry.is_file() and entry.suffix.lower() in source_extensions:
                    try:
                        content = entry.read_text(encoding="utf-8", errors="ignore")
                        for rule_id, rule in AUTH_RISK_PATTERNS.items():
                            for match in re.finditer(rule["pattern"], content, flags=re.MULTILINE | re.IGNORECASE):
                                line_num = content[:match.start()].count("\n") + 1
                                findings.append({
                                    "type": "auth_risk",
                                    "rule": rule_id,
                                    "file": str(entry.relative_to(root)),
                                    "line": line_num,
                                    "severity": "warning",
                                    "message": rule["message"],
                                    "fix": rule["fix"],
                                })
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

    walk(root)
    return findings


def run_security_scan(root: Path) -> dict:
    secrets = scan_for_secrets(root)
    dangerous_files = scan_for_dangerous_files(root)
    auth_risks = scan_auth_risks(root)

    return {
        "secrets": secrets,
        "dangerous_files": dangerous_files,
        "auth_risks": auth_risks,
        "total_findings": len(secrets) + len(dangerous_files) + len(auth_risks),
        "critical_count": sum(1 for f in secrets + dangerous_files + auth_risks if f.get("severity") == "critical"),
    }
