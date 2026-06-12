"""Performance-focused analysis for codeguard."""

from __future__ import annotations

import re
from pathlib import Path

BUNDLE_HEAVY_IMPORTS = {
    "moment": 300,
    "lodash": 70,
    "rxjs": 50,
    "core-js": 80,
    "@material-ui/core": 90,
    "@mui/material": 80,
    "antd": 100,
    "chart.js": 60,
    "three": 150,
    "firebase": 90,
    "@firebase/app": 40,
    "aws-sdk": 200,
    "highlight.js": 70,
    "monaco-editor": 500,
    "pdf-lib": 300,
    "pdfjs-dist": 250,
    "xlsx": 200,
    "mathjs": 170,
    "d3": 100,
    "tensorflow": 2000,
}


def analyze_bundle_risks(js_deps: dict) -> list[dict]:
    findings = []
    for dep, version in js_deps.items():
        dep_lower = dep.lower()
        if dep_lower in BUNDLE_HEAVY_IMPORTS:
            size_kb = BUNDLE_HEAVY_IMPORTS[dep_lower]
            severity = "warning" if size_kb >= 100 else "info"
            findings.append({
                "type": "heavy_import",
                "package": dep,
                "estimated_size_kb": size_kb,
                "severity": severity,
                "message": f"{dep} adds ~{size_kb}KB to bundle. Consider a lighter alternative or lazy loading.",
                "fix": f"Lazy-load {dep} with dynamic import() or consider a smaller alternative.",
            })
    return findings


def analyze_image_patterns(root: Path) -> list[dict]:
    findings = []
    img_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg"}
    large_threshold = 500 * 1024

    def walk(directory: Path):
        try:
            for entry in directory.iterdir():
                if entry.is_dir() and entry.name not in {
                    "node_modules", ".git", "dist", "build", ".next", "vendor", "__pycache__"
                }:
                    walk(entry)
                elif entry.is_file() and entry.suffix.lower() in img_extensions:
                    try:
                        size = entry.stat().st_size
                        if size > large_threshold:
                            findings.append({
                                "type": "large_image",
                                "file": str(entry.relative_to(root)),
                                "size_kb": round(size / 1024),
                                "severity": "warning",
                                "message": f"Large image ({round(size / 1024)}KB). Optimize or convert to WebP/AVIF.",
                                "fix": "Compress with sharp, squoosh, or convert to WebP/AVIF format.",
                            })
                    except OSError:
                        pass
        except (PermissionError, OSError):
            pass

    walk(root)
    return findings


def analyze_missing_optimizations(root: Path, frameworks: list[str]) -> list[dict]:
    findings = []

    if "next.js" in frameworks:
        uses_next_image = False
        uses_next_font = False
        uses_next_dynamic = False
        src_dirs = [root / "src", root / "app", root / "pages", root / "components"]
        for src_dir in src_dirs:
            if not src_dir.exists():
                continue
            for f in src_dir.rglob("*.tsx"):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if "next/image" in content:
                        uses_next_image = True
                    if "next/font" in content:
                        uses_next_font = True
                    if "next/dynamic" in content:
                        uses_next_dynamic = True
                except (PermissionError, OSError):
                    pass
        if not uses_next_image:
            findings.append({
                "type": "missing_optimization",
                "severity": "warning",
                "message": "Next.js project not using next/image. Missing automatic image optimization.",
                "fix": "Use <Image> from next/image for automatic WebP conversion and lazy loading.",
            })
        if not uses_next_font:
            findings.append({
                "type": "missing_optimization",
                "severity": "info",
                "message": "Next.js project not using next/font. Fonts may cause layout shift.",
                "fix": "Use next/font for zero layout shift font loading.",
            })
        if not uses_next_dynamic:
            findings.append({
                "type": "missing_optimization",
                "severity": "info",
                "message": "No dynamic imports found. Heavy components load upfront.",
                "fix": "Use next/dynamic for code splitting heavy components.",
            })

    if "react" in frameworks or "next.js" in frameworks:
        has_memo = False
        has_suspense = False
        for ext in ("*.tsx", "*.jsx"):
            for f in root.rglob(ext):
                if any(skip in f.parts for skip in ("node_modules", ".next", "dist")):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if "React.memo" in content or "useMemo" in content:
                        has_memo = True
                    if "Suspense" in content:
                        has_suspense = True
                except (PermissionError, OSError):
                    pass
        if not has_suspense:
            findings.append({
                "type": "missing_optimization",
                "severity": "info",
                "message": "No React Suspense usage found for code splitting.",
                "fix": "Use React.lazy() + <Suspense> for route-level code splitting.",
            })

    return findings


def run_performance_analysis(root: Path, stack: dict) -> dict:
    js_deps = stack.get("js_deps", {})
    frameworks = stack.get("frameworks", [])

    bundle_risks = analyze_bundle_risks(js_deps)
    image_issues = analyze_image_patterns(root)
    missing_opts = analyze_missing_optimizations(root, frameworks)

    return {
        "bundle_risks": bundle_risks,
        "image_issues": image_issues,
        "missing_optimizations": missing_opts,
        "total_findings": len(bundle_risks) + len(image_issues) + len(missing_opts),
    }
