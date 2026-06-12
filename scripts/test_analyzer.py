"""Test quality and coverage analysis for codeguard."""

from __future__ import annotations

import re
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".next", "dist", ".git", ".pnpm", "__pycache__",
    ".turbo", "build", "coverage", "target", "vendor", ".venv", "venv",
}

TEST_FILE_PATTERNS = {
    "javascript": [
        r"\.test\.(js|jsx|ts|tsx)$",
        r"\.spec\.(js|jsx|ts|tsx)$",
        r"__tests__/.*\.(js|jsx|ts|tsx)$",
    ],
    "python": [
        r"test_\w+\.py$",
        r"\w+_test\.py$",
        r"tests/.*\.py$",
        r"conftest\.py$",
    ],
    "go": [
        r"_test\.go$",
    ],
    "rust": [
        r"tests/.*\.rs$",
    ],
    "php": [
        r"Test\.php$",
        r"tests/.*\.php$",
    ],
    "ruby": [
        r"_spec\.rb$",
        r"_test\.rb$",
        r"spec/.*\.rb$",
        r"test/.*\.rb$",
    ],
    "java": [
        r"Test\.java$",
        r"Tests\.java$",
        r"test/.*\.java$",
    ],
}

TEST_RUNNER_CONFIGS = {
    "jest": ["jest.config.js", "jest.config.ts", "jest.config.mjs"],
    "vitest": ["vitest.config.ts", "vitest.config.js"],
    "pytest": ["pytest.ini", "pyproject.toml", "setup.cfg", "conftest.py"],
    "mocha": [".mocharc.yml", ".mocharc.json"],
    "playwright": ["playwright.config.ts", "playwright.config.js"],
    "cypress": ["cypress.config.js", "cypress.config.ts", "cypress.json"],
    "phpunit": ["phpunit.xml", "phpunit.xml.dist"],
    "rspec": [".rspec"],
    "go-test": ["go.mod"],
    "cargo-test": ["Cargo.toml"],
}

TEST_ANTI_PATTERNS = {
    "snapshot_overuse": {
        "pattern": r"toMatchSnapshot\(\)|toMatchInlineSnapshot\(",
        "severity": "info",
        "message": "Excessive snapshot testing. Snapshots test implementation, not behavior.",
        "fix": "Test behavior and assertions instead of full DOM snapshots.",
    },
    "no_assertion": {
        "pattern": r"it\s*\(\s*['\"].*['\"].*\{[^}]*\}\s*\)(?!.*(?:expect|assert|should))",
        "severity": "warning",
        "message": "Test without assertion. Passes but verifies nothing.",
        "fix": "Add expect() or assert() calls to verify behavior.",
    },
    "test_implementation": {
        "pattern": r"(?:toHaveBeenCalledWith|\.mock\.|jest\.fn\(\)|vi\.fn\(\)){3,}",
        "severity": "info",
        "message": "Heavy mocking — testing implementation details rather than behavior.",
        "fix": "Test outputs and side effects. Reduce mock count.",
    },
    "sleep_in_test": {
        "pattern": r"(?:setTimeout|sleep|wait)\s*\(\s*\d{3,}",
        "severity": "warning",
        "message": "Fixed delay in test. Makes tests slow and flaky.",
        "fix": "Use waitFor, polling, or event-driven assertions.",
    },
    "skip_markers": {
        "pattern": r"(?:\.skip\s*\(|xit\s*\(|xdescribe\s*\(|@pytest\.mark\.skip|@unittest\.skip)",
        "severity": "info",
        "message": "Skipped test found. Track why it was skipped.",
        "fix": "Fix the test or remove it. Don't leave skipped tests forever.",
    },
}

CRITICAL_PATH_KEYWORDS = {
    "auth": ["login", "signup", "register", "logout", "auth", "session", "password", "token", "jwt"],
    "payments": ["payment", "checkout", "stripe", "charge", "subscribe", "billing", "invoice"],
    "data": ["create", "update", "delete", "remove", "migrate", "seed", "import", "export"],
    "api": ["api", "endpoint", "route", "controller", "handler", "middleware"],
    "security": ["sanitize", "validate", "escape", "encrypt", "decrypt", "hash", "verify"],
}


def find_source_files(root: Path, languages: list[str]) -> list[Path]:
    source_exts = set()
    for lang in languages:
        if lang in ("javascript", "typescript"):
            source_exts.update({".js", ".jsx", ".ts", ".tsx"})
        elif lang == "python":
            source_exts.add(".py")
        elif lang == "go":
            source_exts.add(".go")
        elif lang == "rust":
            source_exts.add(".rs")
        elif lang == "php":
            source_exts.add(".php")
        elif lang == "ruby":
            source_exts.add(".rb")
        elif lang == "java":
            source_exts.add(".java")
        elif lang == "csharp":
            source_exts.add(".cs")

    files = []

    def walk(directory: Path):
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        walk(entry)
                elif entry.is_file() and entry.suffix.lower() in source_exts:
                    files.append(entry)
        except (PermissionError, OSError):
            pass

    walk(root)
    return files


def find_test_files(root: Path, languages: list[str]) -> list[Path]:
    test_files = []
    all_patterns = []
    for lang in languages:
        all_patterns.extend(TEST_FILE_PATTERNS.get(lang, []))

    if not all_patterns:
        for patterns in TEST_FILE_PATTERNS.values():
            all_patterns.extend(patterns)

    def walk(directory: Path):
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        walk(entry)
                elif entry.is_file():
                    rel = str(entry.relative_to(root)).replace("\\", "/")
                    for pat in all_patterns:
                        if re.search(pat, rel):
                            test_files.append(entry)
                            break
        except (PermissionError, OSError):
            pass

    walk(root)
    return test_files


def detect_test_runners(root: Path) -> list[str]:
    runners = []
    for runner, configs in TEST_RUNNER_CONFIGS.items():
        for cfg in configs:
            if (root / cfg).exists():
                runners.append(runner)
                break
    return runners


def find_untested_critical_paths(root: Path, source_files: list[Path], test_files: list[Path], languages: list[str]) -> list[dict]:
    test_content = ""
    for tf in test_files:
        try:
            test_content += tf.read_text(encoding="utf-8", errors="ignore").lower() + "\n"
        except (PermissionError, OSError):
            pass

    findings = []
    for sf in source_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore").lower()
            rel = str(sf.relative_to(root))
            stem = sf.stem.lower()

            for category, keywords in CRITICAL_PATH_KEYWORDS.items():
                if any(kw in content for kw in keywords) and any(kw in rel.lower() for kw in keywords):
                    has_test = any(stem in tc for tc in test_content.split("\n") if stem)
                    if not has_test:
                        has_test = any(
                            re.search(rf"(test|spec|describe|it).*{re.escape(stem)}", test_content)
                            for _ in [1]
                        )
                    if not has_test:
                        findings.append({
                            "type": "untested_critical_path",
                            "category": category,
                            "file": rel,
                            "severity": "warning",
                            "message": f"Critical {category} code in {rel} appears untested.",
                            "fix": f"Add tests for {category} logic in {rel}.",
                        })
        except (PermissionError, OSError):
            pass

    return findings


def scan_test_anti_patterns(test_files: list[Path], root: Path) -> list[dict]:
    findings = []
    for tf in test_files:
        try:
            content = tf.read_text(encoding="utf-8", errors="ignore")
            for rule_id, rule in TEST_ANTI_PATTERNS.items():
                for match in re.finditer(rule["pattern"], content, flags=re.MULTILINE):
                    line_num = content[:match.start()].count("\n") + 1
                    findings.append({
                        "type": "test_anti_pattern",
                        "rule": rule_id,
                        "file": str(tf.relative_to(root)),
                        "line": line_num,
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "fix": rule["fix"],
                    })
        except (PermissionError, OSError):
            pass
    return findings


def run_test_analysis(root: Path, languages: list[str]) -> dict:
    source_files = find_source_files(root, languages)
    test_files = find_test_files(root, languages)
    runners = detect_test_runners(root)
    untested = find_untested_critical_paths(root, source_files, test_files, languages)
    anti_patterns = scan_test_anti_patterns(test_files, root)

    source_count = len(source_files)
    test_count = len(test_files)
    ratio = round(test_count / max(source_count, 1) * 100, 1)

    has_unit = any("test" in str(f).lower() or "spec" in str(f).lower() for f in test_files)
    has_integration = any("integration" in str(f).lower() for f in test_files)
    has_e2e = any(
        any(kw in str(f).lower() for kw in ("e2e", "cypress", "playwright", "selenium"))
        for f in test_files
    )

    coverage = "unknown"
    if ratio == 0:
        coverage = "none"
    elif ratio < 20:
        coverage = "low"
    elif ratio < 50:
        coverage = "moderate"
    elif ratio < 80:
        coverage = "good"
    else:
        coverage = "excellent"

    missing_types = []
    if not has_unit:
        missing_types.append("unit")
    if not has_integration:
        missing_types.append("integration")
    if not has_e2e:
        missing_types.append("e2e")

    return {
        "source_file_count": source_count,
        "test_file_count": test_count,
        "test_ratio_percent": ratio,
        "coverage_estimate": coverage,
        "test_runners": runners,
        "has_unit_tests": has_unit,
        "has_integration_tests": has_integration,
        "has_e2e_tests": has_e2e,
        "missing_test_types": missing_types,
        "untested_critical_paths": untested,
        "test_anti_patterns": anti_patterns,
        "total_findings": len(untested) + len(anti_patterns) + len(missing_types),
    }
