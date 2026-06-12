#!/usr/bin/env python3
"""Main orchestrator for the codeguard skill."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Install dependencies first: pip install -r requirements.txt")
    sys.exit(1)

SCRIPT_PATH = Path(__file__).resolve().parent
if str(SCRIPT_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH))

from language_detector import detect_full_stack, find_project_root
from dependency_auditor import audit_dependencies
from pattern_scanner import scan_project
from performance_analyzer import run_performance_analysis
from security_scanner import run_security_scan
from cost_estimator import run_cost_analysis
from test_analyzer import run_test_analysis

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

console = Console(force_terminal=True)
PACKAGE_DIR = SCRIPT_PATH.parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_template(name: str, replacements: dict[str, str] | None = None) -> str:
    content = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "feature"


def severity_icon(severity: str) -> str:
    return {"critical": "!!!", "warning": "!!", "info": "."}.get(severity, ".")


def severity_sort(severity: str) -> int:
    return {"critical": 0, "warning": 1, "info": 2}.get(severity, 3)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        safe = [str(cell).replace("\n", " ").replace("|", "/") for cell in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def ensure_workspace(root: Path):
    codeguard_dir = root / ".codeguard"
    for sub in ("feature-specs", "reviews"):
        (codeguard_dir / sub).mkdir(parents=True, exist_ok=True)
    return codeguard_dir


# ── Artifact generators ───────────────────────────────────────────────────

def generate_report(root: Path, results: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stack = results["stack"]
    deps = results["dependencies"]
    patterns = results["patterns"]
    perf = results["performance"]
    security = results["security"]
    cost = results["cost"]
    tests = results["tests"]

    all_findings = []
    for f in deps["findings"]:
        all_findings.append(f)
    for f in patterns:
        all_findings.append(f)
    for f in perf["bundle_risks"] + perf["image_issues"] + perf["missing_optimizations"]:
        all_findings.append(f)
    for f in security["secrets"] + security["dangerous_files"] + security["auth_risks"]:
        all_findings.append(f)
    for f in cost["services"] + cost["scaling_traps"]:
        all_findings.append(f)
    for f in tests["untested_critical_paths"] + tests["test_anti_patterns"]:
        all_findings.append(f)

    critical = [f for f in all_findings if f.get("severity") == "critical"]
    warnings = [f for f in all_findings if f.get("severity") == "warning"]
    info = [f for f in all_findings if f.get("severity") == "info"]

    lines = [
        f"# Codeguard Report",
        f"",
        f"- Scan Date: {now}",
        f"- Project Root: {root}",
        f"- Total Findings: {len(all_findings)} (Critical: {len(critical)}, Warning: {len(warnings)}, Info: {len(info)})",
        f"",
        f"## Stack Detection",
        f"",
        f"- Primary Language: {stack['primary_language']}",
        f"- Languages: {', '.join(l['name'] + ' (' + str(l['file_count']) + ' files)' for l in stack['languages'][:5])}",
        f"- Frameworks: {', '.join(stack['frameworks']) or 'None detected'}",
        f"- Package Manager: {stack['package_manager']}",
        f"- Build Tools: {', '.join(stack['build_tools']) or 'None detected'}",
        f"- Runtimes: {', '.join(stack['runtimes']) or 'None detected'}",
        f"- Total Dependencies: {deps['total_deps']}",
        f"",
    ]

    if critical:
        lines.append("## Critical Issues (Fix Immediately)")
        lines.append("")
        for f in critical:
            lines.append(f"### !!! {f.get('message', 'Unknown issue')}")
            if f.get("file"):
                lines.append(f"- File: `{f['file']}`" + (f" (line {f['line']})" if f.get("line") else ""))
            if f.get("package"):
                lines.append(f"- Package: `{f['package']}`")
            if f.get("fix"):
                lines.append(f"- Fix: {f['fix']}")
            lines.append("")

    if warnings:
        lines.append("## Warnings (Should Fix)")
        lines.append("")
        for f in warnings:
            lines.append(f"### !! {f.get('message', 'Unknown issue')}")
            if f.get("file"):
                lines.append(f"- File: `{f['file']}`" + (f" (line {f['line']})" if f.get("line") else ""))
            if f.get("package"):
                lines.append(f"- Package: `{f['package']}`")
            if f.get("service"):
                lines.append(f"- Service: {f['service']}")
            if f.get("fix"):
                lines.append(f"- Fix: {f['fix']}")
            lines.append("")

    lines.append("## Dependency Audit")
    lines.append("")
    lines.append(f"- Total Dependencies: {deps['total_deps']}")
    lines.append(f"- Heavy: {deps['heavy_count']}")
    lines.append(f"- Deprecated: {deps['deprecated_count']}")
    lines.append(f"- Cost Risk: {deps['cost_risk_count']}")
    lines.append(f"- Duplicate Functionality: {deps['duplicate_count']}")
    lines.append("")

    lines.append("## Security Summary")
    lines.append("")
    lines.append(f"- Exposed Secrets: {len(security['secrets'])}")
    lines.append(f"- Dangerous Files: {len(security['dangerous_files'])}")
    lines.append(f"- Auth Risks: {len(security['auth_risks'])}")
    lines.append(f"- Critical Security Issues: {security['critical_count']}")
    lines.append("")

    lines.append("## Cost & Scaling Summary")
    lines.append("")
    lines.append(f"- Pay-As-You-Go Services: {cost['service_count']}")
    lines.append(f"- High Risk Services: {cost['high_risk_services']}")
    lines.append(f"- Scaling Traps: {len(cost['scaling_traps'])}")
    lines.append(f"- Overall Monthly Cost Risk: {cost['total_monthly_risk'].upper()}")
    lines.append("")

    if cost["services"]:
        lines.append("### Detected Services")
        lines.append("")
        rows = []
        for s in cost["services"]:
            rows.append([s["service"], s["billing_model"], s["risk_level"].upper(), s["message"][:80]])
        lines.append(markdown_table(["Service", "Billing", "Risk", "Notes"], rows))
        lines.append("")

    lines.append("## Performance Summary")
    lines.append("")
    lines.append(f"- Heavy Bundle Imports: {len(perf['bundle_risks'])}")
    lines.append(f"- Large Images: {len(perf['image_issues'])}")
    lines.append(f"- Missing Optimizations: {len(perf['missing_optimizations'])}")
    lines.append("")

    lines.append("## Test Quality Summary")
    lines.append("")
    lines.append(f"- Source Files: {tests['source_file_count']}")
    lines.append(f"- Test Files: {tests['test_file_count']}")
    lines.append(f"- Test Ratio: {tests['test_ratio_percent']}%")
    lines.append(f"- Coverage Estimate: {tests['coverage_estimate'].upper()}")
    lines.append(f"- Test Runners: {', '.join(tests['test_runners']) or 'None detected'}")
    lines.append(f"- Has Unit Tests: {'Yes' if tests['has_unit_tests'] else 'No'}")
    lines.append(f"- Has Integration Tests: {'Yes' if tests['has_integration_tests'] else 'No'}")
    lines.append(f"- Has E2E Tests: {'Yes' if tests['has_e2e_tests'] else 'No'}")
    lines.append(f"- Missing Test Types: {', '.join(tests['missing_test_types']) or 'None'}")
    lines.append(f"- Untested Critical Paths: {len(tests['untested_critical_paths'])}")
    lines.append("")

    if info:
        lines.append("## Info (Nice To Fix)")
        lines.append("")
        for f in info[:20]:
            lines.append(f"- {f.get('message', 'Unknown')} " + (f"(`{f.get('file', '')}`) " if f.get("file") else "") + (f"— {f.get('fix', '')}" if f.get("fix") else ""))
        if len(info) > 20:
            lines.append(f"- ... and {len(info) - 20} more info-level findings")
        lines.append("")

    return "\n".join(lines)


def generate_plan(root: Path, results: dict) -> str:
    stack = results["stack"]
    deps = results["dependencies"]
    security = results["security"]
    cost = results["cost"]
    tests = results["tests"]

    lines = [
        "# Codeguard Plan",
        "",
        "## Current State",
        "",
        f"- Primary Language: {stack['primary_language']}",
        f"- Frameworks: {', '.join(stack['frameworks']) or 'None'}",
        f"- Security Critical Issues: {security['critical_count']}",
        f"- Cost Risk Level: {cost['total_monthly_risk'].upper()}",
        f"- Test Coverage: {tests['coverage_estimate'].upper()}",
        "",
        "## Priority Order",
        "",
        "1. Fix all CRITICAL security issues (exposed secrets, dangerous files)",
        "2. Fix SQL injection and code injection vulnerabilities",
        "3. Address cost/scaling traps (SQLite in production, no connection pooling)",
        "4. Add missing tests for critical paths (auth, payments, data mutation)",
        "5. Fix deprecated dependencies",
        "6. Address performance issues (heavy imports, large images)",
        "7. Clean up code quality warnings (any types, debug leftovers)",
        "",
        "## Pre-Build Rules",
        "",
        "Before building ANY new feature, the agent must:",
        "",
        "1. Read this PLAN.md and REPORT.md",
        "2. Check if the feature area has known issues",
        "3. Generate a feature spec in `.codeguard/feature-specs/`",
        "4. Include quality constraints from the report",
        "5. Write tests before or alongside implementation",
        "6. Re-scan affected files after implementation",
        "",
        "## Quality Gates",
        "",
        "- [ ] No new critical findings introduced",
        "- [ ] All new endpoints have input validation",
        "- [ ] All new database queries use parameterized statements",
        "- [ ] All new dependencies justified and audited",
        "- [ ] Tests written for new functionality",
        "- [ ] Reduced motion / accessibility considered for UI changes",
        "- [ ] Cost implications documented for new service integrations",
        "",
    ]

    return "\n".join(lines)


def generate_tasks(root: Path, results: dict) -> str:
    all_findings = []
    for f in results["dependencies"]["findings"]:
        all_findings.append({**f, "category": "dependency"})
    for f in results["patterns"]:
        all_findings.append({**f, "category": f.get("category", "pattern")})
    for f in results["security"]["secrets"] + results["security"]["dangerous_files"] + results["security"]["auth_risks"]:
        all_findings.append({**f, "category": "security"})
    for f in results["cost"]["services"] + results["cost"]["scaling_traps"]:
        all_findings.append({**f, "category": "cost"})
    for f in results["performance"]["bundle_risks"] + results["performance"]["image_issues"] + results["performance"]["missing_optimizations"]:
        all_findings.append({**f, "category": "performance"})
    for f in results["tests"]["untested_critical_paths"] + results["tests"]["test_anti_patterns"]:
        all_findings.append({**f, "category": "testing"})
    for mt in results["tests"]["missing_test_types"]:
        all_findings.append({
            "severity": "warning", "category": "testing",
            "message": f"Missing {mt} tests", "fix": f"Add {mt} test suite.",
        })

    all_findings.sort(key=lambda x: severity_sort(x.get("severity", "info")))

    lines = [
        "# Codeguard Tasks",
        "",
        "## Execution Rules",
        "",
        "- Work through tasks by severity: CRITICAL first, then WARNING, then INFO",
        "- Update this file after completing each task",
        "- Re-scan after major changes",
        "",
    ]

    critical = [f for f in all_findings if f.get("severity") == "critical"]
    warning = [f for f in all_findings if f.get("severity") == "warning"]
    info = [f for f in all_findings if f.get("severity") == "info"]

    if critical:
        lines.append("## Critical (Fix Immediately)")
        lines.append("")
        for i, f in enumerate(critical, 1):
            lines.append(f"- [ ] **[{f['category'].upper()}]** {f.get('message', 'Unknown')}")
            if f.get("file"):
                lines.append(f"  - File: `{f['file']}`")
            if f.get("fix"):
                lines.append(f"  - Fix: {f['fix']}")
        lines.append("")

    if warning:
        lines.append("## Warning (Should Fix)")
        lines.append("")
        for i, f in enumerate(warning, 1):
            lines.append(f"- [ ] **[{f['category'].upper()}]** {f.get('message', 'Unknown')}")
            if f.get("file"):
                lines.append(f"  - File: `{f['file']}`")
            if f.get("fix"):
                lines.append(f"  - Fix: {f['fix']}")
        lines.append("")

    if info:
        lines.append("## Info (Nice To Have)")
        lines.append("")
        for i, f in enumerate(info[:30], 1):
            lines.append(f"- [ ] **[{f['category'].upper()}]** {f.get('message', 'Unknown')}")
            if f.get("fix"):
                lines.append(f"  - Fix: {f['fix']}")
        if len(info) > 30:
            lines.append(f"- ... {len(info) - 30} more info-level tasks")
        lines.append("")

    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"- Total Tasks: {len(all_findings)}")
    lines.append(f"- Critical: {len(critical)}")
    lines.append(f"- Warning: {len(warning)}")
    lines.append(f"- Info: {len(info)}")
    lines.append("")

    return "\n".join(lines)


def generate_feature_spec(feature_name: str, results: dict) -> str:
    slug = slugify(feature_name)
    stack = results["stack"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Feature Spec: {feature_name}",
        f"",
        f"- Date: {now}",
        f"- Status: Draft",
        f"- Stack: {stack['primary_language']} / {', '.join(stack['frameworks'][:3]) or 'N/A'}",
        f"",
        f"## Goal",
        f"",
        f"<!-- Describe what this feature does -->",
        f"",
        f"## Affected Files",
        f"",
        f"<!-- List files that will change -->",
        f"",
        f"## Known Risks In This Area",
        f"",
        f"<!-- Auto-populated from REPORT.md -->",
        f"",
        f"## Quality Requirements",
        f"",
        f"- [ ] Input validation at all boundaries",
        f"- [ ] Error handling for all external calls",
        f"- [ ] No hardcoded secrets or magic numbers",
        f"- [ ] Parameterized queries for all DB operations",
        f"- [ ] Tests written (unit + integration where needed)",
        f"- [ ] Performance: no N+1, no unbounded queries",
        f"- [ ] Accessibility: keyboard nav, screen reader, reduced motion",
        f"",
        f"## Cost Impact",
        f"",
        f"- New services: None",
        f"- Estimated cost change: None",
        f"",
        f"## Dependencies Added",
        f"",
        f"- None",
        f"",
        f"## Test Plan",
        f"",
        f"- [ ] Unit tests for core logic",
        f"- [ ] Integration tests for API endpoints",
        f"- [ ] Error case tests",
        f"- [ ] Edge case tests",
        f"",
    ]

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────

def run_full_scan(root: Path) -> dict:
    console.print(Panel("[bold cyan]Codeguard Scan[/] starting...", border_style="cyan"))

    console.print("[dim]Detecting stack...[/]")
    stack = detect_full_stack(root)
    languages = [l["name"] for l in stack["languages"]]

    console.print("[dim]Auditing dependencies...[/]")
    deps = audit_dependencies(stack)

    console.print("[dim]Scanning for anti-patterns...[/]")
    patterns = scan_project(root, languages)

    console.print("[dim]Analyzing performance...[/]")
    perf = run_performance_analysis(root, stack)

    console.print("[dim]Running security scan...[/]")
    security = run_security_scan(root)

    console.print("[dim]Estimating costs and risks...[/]")
    cost = run_cost_analysis(root)

    console.print("[dim]Analyzing test quality...[/]")
    tests = run_test_analysis(root, languages)

    return {
        "stack": stack,
        "dependencies": deps,
        "patterns": patterns,
        "performance": perf,
        "security": security,
        "cost": cost,
        "tests": tests,
    }


def print_summary(results: dict):
    stack = results["stack"]
    table = Table(title="Codeguard Scan Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Findings", style="white")

    table.add_row("Stack", f"{stack['primary_language']} / {', '.join(stack['frameworks'][:3]) or 'N/A'}", "")
    table.add_row("Dependencies", f"{results['dependencies']['total_deps']} total",
                   f"{results['dependencies']['heavy_count']} heavy, {results['dependencies']['deprecated_count']} deprecated")
    table.add_row("Security", f"{'CRITICAL' if results['security']['critical_count'] else 'OK'}",
                   f"{results['security']['total_findings']} findings ({results['security']['critical_count']} critical)")
    table.add_row("Cost Risk", results['cost']['total_monthly_risk'].upper(),
                   f"{results['cost']['service_count']} services, {len(results['cost']['scaling_traps'])} traps")
    table.add_row("Performance", f"{results['performance']['total_findings']} issues", "")
    table.add_row("Tests", results['tests']['coverage_estimate'].upper(),
                   f"{results['tests']['test_file_count']}/{results['tests']['source_file_count']} ratio")
    table.add_row("Patterns", f"{len(results['patterns'])} findings", "")

    console.print(table)


@click.group()
def cli():
    """Codeguard — spec-driven code quality guardian."""


@cli.command(name="scan")
@click.option("--path", default=".", help="Project root path")
def cmd_scan(path):
    """Run a full project scan and generate REPORT.md, PLAN.md, TASKS.md."""
    root = find_project_root(path)
    codeguard_dir = ensure_workspace(root)

    results = run_full_scan(root)

    report_content = generate_report(root, results)
    plan_content = generate_plan(root, results)
    tasks_content = generate_tasks(root, results)

    write_text(codeguard_dir / "REPORT.md", report_content)
    write_text(codeguard_dir / "PLAN.md", plan_content)
    write_text(codeguard_dir / "TASKS.md", tasks_content)

    console.print(f"\n[green]Created[/] {codeguard_dir / 'REPORT.md'}")
    console.print(f"[green]Created[/] {codeguard_dir / 'PLAN.md'}")
    console.print(f"[green]Created[/] {codeguard_dir / 'TASKS.md'}")
    console.print()
    print_summary(results)

    critical_count = results["security"]["critical_count"] + sum(
        1 for f in results["dependencies"]["findings"] if f.get("severity") == "critical"
    ) + sum(1 for f in results["patterns"] if f.get("severity") == "critical")

    if critical_count:
        console.print(f"\n[bold red]!!! {critical_count} CRITICAL issues found. Fix these before building new features. !!![/]")


@cli.command(name="review")
@click.option("--path", default=".", help="Project root path")
@click.option("--feature", required=True, help="Feature name for the review")
def cmd_review(path, feature):
    """Run a targeted review for a feature and generate a feature spec."""
    root = find_project_root(path)
    codeguard_dir = ensure_workspace(root)
    slug = slugify(feature)

    report_path = codeguard_dir / "REPORT.md"
    if not report_path.exists():
        console.print("[yellow]No existing scan found. Running full scan first...[/]\n")
        results = run_full_scan(root)
        write_text(report_path, generate_report(root, results))
        write_text(codeguard_dir / "PLAN.md", generate_plan(root, results))
        write_text(codeguard_dir / "TASKS.md", generate_tasks(root, results))
    else:
        console.print("[dim]Existing scan found. Running fresh scan for accuracy...[/]")
        results = run_full_scan(root)
        write_text(report_path, generate_report(root, results))
        write_text(codeguard_dir / "PLAN.md", generate_plan(root, results))
        write_text(codeguard_dir / "TASKS.md", generate_tasks(root, results))

    spec_content = generate_feature_spec(feature, results)
    spec_path = codeguard_dir / "feature-specs" / f"{slug}.spec.md"
    write_text(spec_path, spec_content)

    console.print(f"\n[green]Created[/] {spec_path}")
    console.print()
    print_summary(results)

    console.print(Panel(
        f"[bold cyan]Feature Review: {feature}[/]\n"
        f"[dim]Spec: {spec_path}[/]\n"
        f"[dim]Read REPORT.md for known risks in the affected area.[/]",
        border_style="cyan",
    ))


@cli.command(name="_status", hidden=True)
@click.option("--path", default=".", help="Project root path")
def cmd_status(path):
    """Show current .codeguard artifact status."""
    root = find_project_root(path)
    codeguard_dir = root / ".codeguard"
    table = Table(title=".codeguard Status")
    table.add_column("Artifact")
    table.add_column("Present")
    for name in ["REPORT.md", "PLAN.md", "TASKS.md", "feature-specs", "reviews"]:
        target = codeguard_dir / name
        table.add_row(name, "yes" if target.exists() else "no")
    console.print(table)


def main():
    cli()


if __name__ == "__main__":
    main()
