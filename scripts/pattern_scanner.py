"""Anti-pattern and heavy code pattern scanner for codeguard."""

from __future__ import annotations

import re
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".next", "dist", ".git", ".pnpm", "__pycache__",
    ".turbo", "build", "coverage", "target", "vendor", ".venv", "venv",
    "env", ".tox", ".mypy_cache", ".pytest_cache", "bin", "obj",
    ".gradle", ".idea", ".vs", ".vscode",
}

SOURCE_EXTENSIONS = (
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".py", ".pyx",
    ".go",
    ".rs",
    ".java",
    ".cs",
    ".php",
    ".rb",
    ".swift", ".kt",
    ".vue", ".svelte",
)

# ── General patterns (all languages) ──────────────────────────────────────

GENERAL_PATTERNS = {
    "hardcoded_secret": {
        "pattern": r"""(?:api[_-]?key|password|secret|token|auth|credential)\s*[:=]\s*['"][A-Za-z0-9+/=_\-]{16,}['"]""",
        "severity": "critical",
        "message": "Hardcoded secret or API key detected. Use environment variables.",
        "fix": "Move to .env file and load via process.env or os.environ.",
    },
    "exposed_env_in_client": {
        "pattern": r"(?:NEXT_PUBLIC|VITE|REACT_APP)_.*?(?:SECRET|KEY|TOKEN|PASSWORD)",
        "severity": "critical",
        "message": "Secret exposed to client via public env prefix.",
        "fix": "Remove SECRET/KEY/TOKEN from client-exposed env vars. Use server-side API routes.",
    },
    "console_log_leftover": {
        "pattern": r"console\.log\(",
        "severity": "info",
        "message": "console.log leftover found. Remove before production.",
        "fix": "Remove or replace with a proper logger.",
    },
    "debug_leftover": {
        "pattern": r"(?:debugger;|import\s+pdb|pdb\.set_trace|breakpoint\(\)|dd\(|var_dump\(|dump\(|print_r\()",
        "severity": "warning",
        "message": "Debug statement leftover detected.",
        "fix": "Remove debug statements before committing.",
    },
    "todo_fixme": {
        "pattern": r"(?:TODO|FIXME|HACK|XXX|TEMP|TEMPORARY)\b",
        "severity": "info",
        "message": "TODO/FIXME marker found. Track these.",
        "fix": "Resolve or create an issue to track it.",
    },
    "magic_number": {
        "pattern": r"(?:if|while|for|return|==|!=|>=|<=|>|<)\s*(?:\d{3,})\b",
        "severity": "info",
        "message": "Magic number detected. Use named constants.",
        "fix": "Extract to a named constant with clear meaning.",
    },
    "deep_nesting": {
        "pattern": r"(?:^\s{16,}(?:if|for|while|switch|match))",
        "severity": "warning",
        "message": "Deeply nested code (4+ levels). Refactor for readability.",
        "fix": "Extract inner blocks to functions. Use early returns or guard clauses.",
    },
}

# ── JavaScript / TypeScript patterns ──────────────────────────────────────

JS_PATTERNS = {
    "any_type": {
        "pattern": r":\s*any\b",
        "severity": "warning",
        "message": "TypeScript 'any' type defeats type safety.",
        "fix": "Use a specific type, unknown, or a generic.",
        "extensions": (".ts", ".tsx"),
    },
    "ts_ignore": {
        "pattern": r"@ts-ignore|@ts-nocheck|@ts-expect-error",
        "severity": "warning",
        "message": "TypeScript error suppression found.",
        "fix": "Fix the underlying type error instead of suppressing.",
        "extensions": (".ts", ".tsx"),
    },
    "useeffect_no_deps": {
        "pattern": r"useEffect\(\s*\(\)\s*=>\s*\{[^}]*\}\s*\)\s*;",
        "severity": "warning",
        "message": "useEffect without dependency array runs on every render.",
        "fix": "Add a dependency array. Use [] for mount-only effects.",
        "extensions": (".jsx", ".tsx"),
    },
    "index_as_key": {
        "pattern": r"\.map\([^)]*,?\s*(?:index|i|idx)\s*\)\s*=>[^}]*key\s*=\s*\{?\s*(?:index|i|idx)\s*\}?",
        "severity": "warning",
        "message": "Array index used as React key. Causes re-render bugs.",
        "fix": "Use a stable unique ID as key.",
        "extensions": (".jsx", ".tsx"),
    },
    "sync_fs": {
        "pattern": r"(?:readFileSync|writeFileSync|appendFileSync|existsSync|mkdirSync)\(",
        "severity": "warning",
        "message": "Synchronous file operation blocks the event loop.",
        "fix": "Use async versions (readFile, writeFile) with await.",
        "extensions": (".js", ".ts", ".mjs", ".cjs"),
    },
    "eval_usage": {
        "pattern": r"\beval\s*\(",
        "severity": "critical",
        "message": "eval() is a code injection risk.",
        "fix": "Remove eval. Use JSON.parse or a safe alternative.",
        "extensions": (".js", ".jsx", ".ts", ".tsx"),
    },
    "innerhtml": {
        "pattern": r"(?:innerHTML|dangerouslySetInnerHTML|v-html)",
        "severity": "warning",
        "message": "Direct HTML injection is an XSS risk.",
        "fix": "Sanitize input with DOMPurify or use safe rendering.",
        "extensions": (".js", ".jsx", ".ts", ".tsx", ".vue"),
    },
    "fetch_no_error": {
        "pattern": r"await\s+fetch\([^)]+\)\s*(?:;|\n)(?!\s*(?:\.then|\.catch|if\s*\(!|const\s+\{?\s*(?:ok|status)))",
        "severity": "warning",
        "message": "fetch() without error handling. Network errors will crash.",
        "fix": "Wrap in try/catch or check response.ok.",
        "extensions": (".js", ".jsx", ".ts", ".tsx"),
    },
    "no_cors_config": {
        "pattern": r"""cors\(\s*\)""",
        "severity": "warning",
        "message": "CORS with no configuration allows all origins.",
        "fix": "Specify allowed origins: cors({ origin: 'https://yourdomain.com' })",
        "extensions": (".js", ".ts"),
    },
}

# ── Python patterns ───────────────────────────────────────────────────────

PYTHON_PATTERNS = {
    "bare_except": {
        "pattern": r"except\s*:",
        "severity": "warning",
        "message": "Bare except catches everything including SystemExit and KeyboardInterrupt.",
        "fix": "Use except Exception: or catch specific exceptions.",
        "extensions": (".py",),
    },
    "mutable_default": {
        "pattern": r"def\s+\w+\([^)]*(?:=\s*\[\]|=\s*\{\}|=\s*set\(\))",
        "severity": "warning",
        "message": "Mutable default argument. Shared across calls.",
        "fix": "Use None as default and create inside the function.",
        "extensions": (".py",),
    },
    "star_import": {
        "pattern": r"from\s+\S+\s+import\s+\*",
        "severity": "warning",
        "message": "Star import pollutes namespace and hides dependencies.",
        "fix": "Import specific names.",
        "extensions": (".py",),
    },
    "sql_string_format": {
        "pattern": r"""(?:execute|cursor\.execute)\s*\(\s*f?['"]+.*\{.*\}""",
        "severity": "critical",
        "message": "SQL query built with string formatting. SQL injection risk.",
        "fix": "Use parameterized queries with placeholders.",
        "extensions": (".py",),
    },
    "no_type_hints": {
        "pattern": r"def\s+\w+\(\s*self\s*,\s*\w+\s*(?:,\s*\w+\s*)*\)\s*:",
        "severity": "info",
        "message": "Function parameters without type hints.",
        "fix": "Add type hints for better IDE support and documentation.",
        "extensions": (".py",),
    },
    "global_state": {
        "pattern": r"^\s*global\s+\w+",
        "severity": "warning",
        "message": "Global keyword usage. Makes code harder to test and reason about.",
        "fix": "Pass state as function parameters or use dependency injection.",
        "extensions": (".py",),
    },
    "sync_sleep": {
        "pattern": r"time\.sleep\(",
        "severity": "info",
        "message": "time.sleep blocks the thread. Use asyncio.sleep in async code.",
        "fix": "Use asyncio.sleep() in async contexts.",
        "extensions": (".py",),
    },
}

# ── Go patterns ───────────────────────────────────────────────────────────

GO_PATTERNS = {
    "unchecked_error": {
        "pattern": r"\w+,\s*_\s*:?=\s*\w+\.\w+\(",
        "severity": "warning",
        "message": "Error return value discarded with _.",
        "fix": "Handle errors explicitly. At minimum, log them.",
        "extensions": (".go",),
    },
    "goroutine_no_recover": {
        "pattern": r"go\s+func\s*\([^)]*\)\s*\{(?![\s\S]*?recover)",
        "severity": "warning",
        "message": "Goroutine without recover. Panics will crash the program.",
        "fix": "Add defer/recover at the top of goroutine functions.",
        "extensions": (".go",),
    },
    "fmt_in_production": {
        "pattern": r"fmt\.Print",
        "severity": "info",
        "message": "fmt.Print in production code. Use a structured logger.",
        "fix": "Use log/slog or a structured logging library.",
        "extensions": (".go",),
    },
}

# ── PHP patterns ──────────────────────────────────────────────────────────

PHP_PATTERNS = {
    "sql_concat": {
        "pattern": r"""(?:\$\w+\s*\.\s*['"](?:SELECT|INSERT|UPDATE|DELETE|WHERE))|(?:query\s*\(\s*['"].*\$)""",
        "severity": "critical",
        "message": "SQL built with string concatenation. SQL injection risk.",
        "fix": "Use prepared statements with PDO or Eloquent.",
        "extensions": (".php",),
    },
    "extract_usage": {
        "pattern": r"\bextract\s*\(",
        "severity": "warning",
        "message": "extract() creates variables from user input. Security risk.",
        "fix": "Access array values directly.",
        "extensions": (".php",),
    },
    "error_display": {
        "pattern": r"(?:display_errors|error_reporting\s*\(\s*E_ALL\s*\))",
        "severity": "warning",
        "message": "Error display enabled. Leaks server info in production.",
        "fix": "Disable display_errors in production. Log errors instead.",
        "extensions": (".php",),
    },
}

# ── Ruby patterns ─────────────────────────────────────────────────────────

RUBY_PATTERNS = {
    "mass_assignment": {
        "pattern": r"params\.permit!",
        "severity": "critical",
        "message": "permit! allows all params. Mass assignment vulnerability.",
        "fix": "Whitelist specific params with permit(:name, :email).",
        "extensions": (".rb",),
    },
    "raw_sql": {
        "pattern": r"""(?:execute|find_by_sql|where)\s*\(\s*['"].*#\{""",
        "severity": "critical",
        "message": "SQL with string interpolation. SQL injection risk.",
        "fix": "Use parameterized queries: where('name = ?', name).",
        "extensions": (".rb",),
    },
}

# ── Performance patterns (all languages) ──────────────────────────────────

PERFORMANCE_PATTERNS = {
    "n_plus_1_loop": {
        "pattern": r"""(?:for\s*\([^)]*\)\s*\{[^}]*await\s+\w+\.(?:find|get|fetch|query))|(?:\.forEach\(\s*async)|(?:for\s+\w+\s+in\s+\w+:\s*\n\s+\w+\.objects\.(?:get|filter))""",
        "severity": "warning",
        "message": "Possible N+1 query pattern: database call inside a loop.",
        "fix": "Batch the query outside the loop. Use .findMany(), .in_bulk(), or eager loading.",
    },
    "no_pagination": {
        "pattern": r"""(?:\.find\(\s*\{\s*\}\s*\))|(?:\.findMany\(\s*\))|(?:\.objects\.all\(\))|(?:SELECT\s+\*\s+FROM\s+\w+\s*;?\s*$)""",
        "severity": "warning",
        "message": "Query returns all records without pagination.",
        "fix": "Add .limit()/.take()/.paginate() or cursor-based pagination.",
    },
    "load_all_in_memory": {
        "pattern": r"""(?:JSON\.parse\(\s*(?:fs\.)?readFileSync)|(?:\.read\(\)\.split\()|(?:pd\.read_csv\([^)]*\)\s*(?!.*chunksize))""",
        "severity": "warning",
        "message": "Loading entire file/dataset into memory.",
        "fix": "Use streaming, chunking, or pagination for large data.",
    },
    "unbounded_loop": {
        "pattern": r"while\s*\(\s*true\s*\)|while\s+True\s*:",
        "severity": "info",
        "message": "Unbounded loop detected. Ensure there's a break condition.",
        "fix": "Add explicit break conditions and maximum iteration limits.",
    },
}

# ── Database risk patterns ────────────────────────────────────────────────

DB_RISK_PATTERNS = {
    "sqlite_in_production": {
        "pattern": r"""(?:sqlite3|better-sqlite3|django\.db\.backends\.sqlite3|DATABASE_URL.*?sqlite|\.sqlite3?|file:.*\.db)""",
        "severity": "warning",
        "message": "SQLite detected. Not suitable for production at scale (single-writer, no concurrent writes).",
        "fix": "Migrate to PostgreSQL or MySQL for production. SQLite is fine for development.",
    },
    "no_connection_pool": {
        "pattern": r"""(?:mysql\.createConnection|pg\.Client\(|psycopg2\.connect\()""",
        "severity": "warning",
        "message": "Direct DB connection without pooling. Will exhaust connections under load.",
        "fix": "Use a connection pool: mysql.createPool(), pg.Pool, or SQLAlchemy pool.",
    },
    "raw_sql_no_param": {
        "pattern": r"""(?:\.query|\.execute)\s*\(\s*(?:`|f?['"]).*?(?:\$\{|\{|%s|%d|\+\s*\w+)""",
        "severity": "critical",
        "message": "Raw SQL with string interpolation. SQL injection vulnerability.",
        "fix": "Use parameterized queries with placeholders (?, $1, %s).",
    },
}

ALL_PATTERN_SETS = {
    "general": GENERAL_PATTERNS,
    "javascript": JS_PATTERNS,
    "typescript": JS_PATTERNS,
    "python": PYTHON_PATTERNS,
    "go": GO_PATTERNS,
    "php": PHP_PATTERNS,
    "ruby": RUBY_PATTERNS,
    "performance": PERFORMANCE_PATTERNS,
    "database": DB_RISK_PATTERNS,
}


def scan_file(file_path: Path, content: str, languages: list[str]) -> list[dict]:
    findings = []
    suffix = file_path.suffix.lower()

    pattern_sets_to_use = ["general", "performance", "database"]
    for lang in languages:
        if lang in ALL_PATTERN_SETS:
            pattern_sets_to_use.append(lang)

    for set_name in pattern_sets_to_use:
        patterns = ALL_PATTERN_SETS.get(set_name, {})
        for rule_id, rule in patterns.items():
            if "extensions" in rule and suffix not in rule["extensions"]:
                continue
            try:
                for match in re.finditer(rule["pattern"], content, flags=re.MULTILINE | re.IGNORECASE):
                    line_num = content[:match.start()].count("\n") + 1
                    findings.append({
                        "rule": rule_id,
                        "category": set_name,
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "fix": rule.get("fix", ""),
                        "file": str(file_path),
                        "line": line_num,
                        "match": match.group(0)[:120],
                    })
            except re.error:
                continue
    return findings


def scan_project(root: Path, languages: list[str], max_files: int = 500) -> list[dict]:
    all_findings = []
    file_count = 0

    def walk(directory: Path):
        nonlocal file_count
        try:
            for entry in sorted(directory.iterdir()):
                if file_count >= max_files:
                    return
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        walk(entry)
                elif entry.is_file() and entry.suffix.lower() in SOURCE_EXTENSIONS:
                    file_count += 1
                    try:
                        content = entry.read_text(encoding="utf-8", errors="ignore")
                        findings = scan_file(entry, content, languages)
                        for f in findings:
                            f["file"] = str(entry.relative_to(root))
                        all_findings.extend(findings)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

    walk(root)
    return all_findings
