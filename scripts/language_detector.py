"""Language, framework, and toolchain detection for codeguard."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

LANGUAGE_EXTENSIONS = {
    "python": (".py", ".pyx", ".pyi"),
    "javascript": (".js", ".jsx", ".mjs", ".cjs"),
    "typescript": (".ts", ".tsx", ".mts", ".cts"),
    "go": (".go",),
    "rust": (".rs",),
    "java": (".java",),
    "csharp": (".cs",),
    "php": (".php",),
    "ruby": (".rb",),
    "swift": (".swift",),
    "kotlin": (".kt", ".kts"),
    "dart": (".dart",),
    "c": (".c", ".h"),
    "cpp": (".cpp", ".cc", ".cxx", ".hpp", ".hxx"),
    "lua": (".lua",),
    "elixir": (".ex", ".exs"),
    "scala": (".scala",),
    "r": (".r", ".R"),
    "shell": (".sh", ".bash", ".zsh"),
}

LANGUAGE_MARKERS = {
    "python": ("requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "setup.cfg", "poetry.lock"),
    "javascript": ("package.json",),
    "typescript": ("tsconfig.json", "tsconfig.base.json"),
    "go": ("go.mod", "go.sum"),
    "rust": ("Cargo.toml", "Cargo.lock"),
    "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    "csharp": (".csproj", ".sln", ".fsproj"),
    "php": ("composer.json", "composer.lock"),
    "ruby": ("Gemfile", "Gemfile.lock", ".ruby-version"),
    "swift": ("Package.swift",),
    "kotlin": ("build.gradle.kts",),
    "dart": ("pubspec.yaml",),
    "elixir": ("mix.exs",),
    "scala": ("build.sbt",),
}

FRAMEWORK_PATTERNS = {
    "next.js": {"marker_deps": ["next"], "config_files": ["next.config.js", "next.config.ts", "next.config.mjs"]},
    "react": {"marker_deps": ["react", "react-dom"], "config_files": []},
    "vue": {"marker_deps": ["vue"], "config_files": ["vue.config.js", "nuxt.config.ts", "nuxt.config.js"]},
    "nuxt": {"marker_deps": ["nuxt"], "config_files": ["nuxt.config.ts", "nuxt.config.js"]},
    "svelte": {"marker_deps": ["svelte"], "config_files": ["svelte.config.js"]},
    "sveltekit": {"marker_deps": ["@sveltejs/kit"], "config_files": ["svelte.config.js"]},
    "angular": {"marker_deps": ["@angular/core"], "config_files": ["angular.json"]},
    "astro": {"marker_deps": ["astro"], "config_files": ["astro.config.mjs", "astro.config.ts"]},
    "remix": {"marker_deps": ["@remix-run/react"], "config_files": []},
    "gatsby": {"marker_deps": ["gatsby"], "config_files": ["gatsby-config.js", "gatsby-config.ts"]},
    "express": {"marker_deps": ["express"], "config_files": []},
    "fastify": {"marker_deps": ["fastify"], "config_files": []},
    "nestjs": {"marker_deps": ["@nestjs/core"], "config_files": ["nest-cli.json"]},
    "django": {"marker_deps": ["django", "Django"], "config_files": ["manage.py"]},
    "flask": {"marker_deps": ["flask", "Flask"], "config_files": []},
    "fastapi": {"marker_deps": ["fastapi"], "config_files": []},
    "spring-boot": {"marker_deps": ["spring-boot-starter"], "config_files": ["application.properties", "application.yml"]},
    "laravel": {"marker_deps": ["laravel/framework"], "config_files": ["artisan"]},
    "rails": {"marker_deps": ["rails"], "config_files": ["Rakefile", "config/routes.rb"]},
    "gin": {"marker_deps": ["github.com/gin-gonic/gin"], "config_files": []},
    "fiber": {"marker_deps": ["github.com/gofiber/fiber"], "config_files": []},
    "actix-web": {"marker_deps": ["actix-web"], "config_files": []},
    "rocket": {"marker_deps": ["rocket"], "config_files": []},
    "flutter": {"marker_deps": ["flutter"], "config_files": []},
    "electron": {"marker_deps": ["electron"], "config_files": []},
    "tauri": {"marker_deps": ["tauri"], "config_files": ["tauri.conf.json"]},
    "react-native": {"marker_deps": ["react-native"], "config_files": ["app.json"]},
}

PACKAGE_MANAGERS = {
    "pnpm": "pnpm-lock.yaml",
    "yarn": "yarn.lock",
    "bun": "bun.lockb",
    "npm": "package-lock.json",
    "pip": "requirements.txt",
    "poetry": "poetry.lock",
    "pipenv": "Pipfile.lock",
    "uv": "uv.lock",
    "cargo": "Cargo.lock",
    "go-modules": "go.sum",
    "composer": "composer.lock",
    "bundler": "Gemfile.lock",
    "maven": "pom.xml",
    "gradle": "build.gradle",
    "pub": "pubspec.lock",
    "mix": "mix.lock",
    "nuget": "packages.config",
}

BUILD_TOOLS = {
    "vite": ("vite.config.js", "vite.config.ts", "vite.config.mjs"),
    "webpack": ("webpack.config.js", "webpack.config.ts"),
    "esbuild": ("esbuild.config.js",),
    "turbopack": ("turbo.json",),
    "rollup": ("rollup.config.js", "rollup.config.mjs"),
    "parcel": (".parcelrc",),
    "tsup": ("tsup.config.ts",),
    "swc": (".swcrc",),
    "babel": ("babel.config.js", ".babelrc"),
    "make": ("Makefile",),
    "cmake": ("CMakeLists.txt",),
    "docker": ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"),
}

SKIP_DIRS = {
    "node_modules", ".next", "dist", ".git", ".pnpm", "__pycache__",
    ".turbo", "build", "coverage", "target", "vendor", ".venv", "venv",
    "env", ".env", ".tox", ".mypy_cache", ".pytest_cache", "bin", "obj",
    ".gradle", ".idea", ".vs", ".vscode",
}


def find_project_root(start_path: str = ".") -> Path:
    path = Path(start_path).resolve()
    markers = ("package.json", "pyproject.toml", "go.mod", "Cargo.toml",
               "pom.xml", "composer.json", "Gemfile", ".git")
    while path != path.parent:
        if any((path / m).exists() for m in markers):
            return path
        path = path.parent
    return Path(start_path).resolve()


def count_files_by_extension(root: Path) -> Counter:
    counts = Counter()

    def walk(directory: Path):
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        walk(entry)
                elif entry.is_file():
                    counts[entry.suffix.lower()] += 1
        except (PermissionError, OSError):
            pass

    walk(root)
    return counts


def detect_languages(root: Path) -> list[dict]:
    ext_counts = count_files_by_extension(root)
    languages = []

    for lang, extensions in LANGUAGE_EXTENSIONS.items():
        count = sum(ext_counts.get(ext, 0) for ext in extensions)
        if count == 0:
            continue
        has_marker = False
        if lang in LANGUAGE_MARKERS:
            for marker in LANGUAGE_MARKERS[lang]:
                if marker.startswith("."):
                    for f in root.rglob(f"*{marker}"):
                        if not any(p in SKIP_DIRS for p in f.parts):
                            has_marker = True
                            break
                elif (root / marker).exists():
                    has_marker = True
                    break
        languages.append({
            "name": lang,
            "file_count": count,
            "has_marker": has_marker,
            "confidence": "high" if has_marker or count > 5 else "low",
        })

    languages.sort(key=lambda x: (-x["file_count"],))
    return languages


def load_deps_from_package_json(root: Path) -> dict:
    for candidate in [root, root / "apps" / "web", root / "frontend", root / "client"]:
        pkg = candidate / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                return {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
            except Exception:
                continue
    return {}


def load_deps_from_python(root: Path) -> list[str]:
    deps = []
    req = root / "requirements.txt"
    if req.exists():
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                name = re.split(r"[>=<!\[\];]", line)[0].strip()
                if name:
                    deps.append(name.lower())
    toml = root / "pyproject.toml"
    if toml.exists():
        content = toml.read_text(encoding="utf-8")
        for match in re.findall(r'"([a-zA-Z0-9_-]+)(?:\[.*?\])?(?:[>=<].*?)?"', content):
            deps.append(match.lower())
    return list(set(deps))


def load_deps_from_go(root: Path) -> list[str]:
    gomod = root / "go.mod"
    if not gomod.exists():
        return []
    deps = []
    for line in gomod.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("module") and not line.startswith("go ") and not line.startswith("//"):
            parts = line.split()
            if parts and "/" in parts[0]:
                deps.append(parts[0])
    return deps


def load_deps_from_cargo(root: Path) -> list[str]:
    cargo = root / "Cargo.toml"
    if not cargo.exists():
        return []
    deps = []
    in_deps = False
    for line in cargo.read_text(encoding="utf-8").splitlines():
        if re.match(r"\[.*dependencies.*\]", line):
            in_deps = True
            continue
        if line.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps:
            match = re.match(r'^(\S+)\s*=', line)
            if match:
                deps.append(match.group(1))
    return deps


def detect_frameworks(root: Path, js_deps: dict, py_deps: list, go_deps: list, cargo_deps: list) -> list[str]:
    detected = []
    all_dep_names = set(js_deps.keys()) | set(py_deps) | set(go_deps) | set(cargo_deps)

    for framework, info in FRAMEWORK_PATTERNS.items():
        found = False
        for dep in info["marker_deps"]:
            if any(dep in d for d in all_dep_names):
                found = True
                break
        if not found:
            for cfg in info["config_files"]:
                if (root / cfg).exists():
                    found = True
                    break
        if found:
            detected.append(framework)
    return detected


def detect_package_manager(root: Path) -> str:
    for pm, lockfile in PACKAGE_MANAGERS.items():
        if (root / lockfile).exists():
            return pm
    return "unknown"


def detect_build_tools(root: Path) -> list[str]:
    tools = []
    for tool, configs in BUILD_TOOLS.items():
        for cfg in configs:
            if (root / cfg).exists():
                tools.append(tool)
                break
    return tools


def detect_runtime(root: Path) -> list[str]:
    runtimes = []
    if (root / ".node-version").exists() or (root / ".nvmrc").exists():
        runtimes.append("node")
    if (root / ".python-version").exists() or (root / "runtime.txt").exists():
        runtimes.append("python")
    if (root / "Dockerfile").exists():
        runtimes.append("docker")
    if (root / "fly.toml").exists():
        runtimes.append("fly.io")
    if (root / "vercel.json").exists() or (root / ".vercel").exists():
        runtimes.append("vercel")
    if (root / "netlify.toml").exists():
        runtimes.append("netlify")
    if (root / "railway.json").exists() or (root / "railway.toml").exists():
        runtimes.append("railway")
    if (root / "render.yaml").exists():
        runtimes.append("render")
    if (root / "Procfile").exists():
        runtimes.append("heroku")
    if (root / "app.yaml").exists() or (root / "app.yml").exists():
        runtimes.append("gcp-app-engine")
    if any((root / f).exists() for f in ("serverless.yml", "serverless.yaml", "serverless.ts")):
        runtimes.append("serverless")
    if (root / "terraform").exists() or (root / "main.tf").exists():
        runtimes.append("terraform")
    return runtimes


def detect_full_stack(root: Path) -> dict:
    languages = detect_languages(root)
    js_deps = load_deps_from_package_json(root)
    py_deps = load_deps_from_python(root)
    go_deps = load_deps_from_go(root)
    cargo_deps = load_deps_from_cargo(root)
    frameworks = detect_frameworks(root, js_deps, py_deps, go_deps, cargo_deps)
    package_manager = detect_package_manager(root)
    build_tools = detect_build_tools(root)
    runtimes = detect_runtime(root)

    primary_language = languages[0]["name"] if languages else "unknown"

    return {
        "root": root,
        "languages": languages,
        "primary_language": primary_language,
        "frameworks": frameworks,
        "package_manager": package_manager,
        "build_tools": build_tools,
        "runtimes": runtimes,
        "js_deps": js_deps,
        "py_deps": py_deps,
        "go_deps": go_deps,
        "cargo_deps": cargo_deps,
        "all_deps": {**js_deps, **{d: "*" for d in py_deps + go_deps + cargo_deps}},
    }
