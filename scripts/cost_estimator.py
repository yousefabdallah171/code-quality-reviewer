"""Cost and risk estimation for pay-as-you-go services and scaling traps."""

from __future__ import annotations

import re
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".next", "dist", ".git", ".pnpm", "__pycache__",
    ".turbo", "build", "coverage", "target", "vendor", ".venv", "venv",
}

SERVICE_COST_PROFILES = {
    "openai": {
        "name": "OpenAI API",
        "model": "per-token",
        "risk_level": "high",
        "env_keys": ["OPENAI_API_KEY"],
        "code_patterns": [r"openai\.", r"from openai import", r"ChatCompletion", r"openai\.chat"],
        "warning": "Token-based billing. GPT-4 costs $30-60/M tokens. Unbounded calls can spike to hundreds of dollars.",
        "mitigation": "Set usage limits in OpenAI dashboard. Add request rate limiting. Cache responses. Use cheaper models for simple tasks.",
    },
    "anthropic": {
        "name": "Anthropic API",
        "model": "per-token",
        "risk_level": "high",
        "env_keys": ["ANTHROPIC_API_KEY"],
        "code_patterns": [r"anthropic\.", r"from anthropic import", r"messages\.create"],
        "warning": "Token-based billing. Claude costs vary by model. Monitor usage.",
        "mitigation": "Set spending limits. Cache responses. Use Haiku for simple tasks.",
    },
    "aws_s3": {
        "name": "AWS S3",
        "model": "storage+transfer",
        "risk_level": "medium",
        "env_keys": ["AWS_ACCESS_KEY_ID", "AWS_BUCKET"],
        "code_patterns": [r"S3Client", r"PutObjectCommand", r"s3\.upload", r"boto3.*s3"],
        "warning": "Storage ($0.023/GB/month) + data transfer out ($0.09/GB). Large files or high traffic = cost.",
        "mitigation": "Set lifecycle policies. Use CloudFront CDN. Compress before upload.",
    },
    "aws_lambda": {
        "name": "AWS Lambda",
        "model": "per-invocation",
        "risk_level": "medium",
        "env_keys": ["AWS_LAMBDA_FUNCTION_NAME"],
        "code_patterns": [r"exports\.handler", r"lambda_handler", r"@app\.lambda_function"],
        "warning": "Per-invocation + duration billing. Cold starts add latency. Recursive triggers can bankrupt.",
        "mitigation": "Set concurrency limits. Add circuit breakers. Monitor invocation counts.",
    },
    "firebase_firestore": {
        "name": "Firebase Firestore",
        "model": "per-read/write",
        "risk_level": "high",
        "env_keys": ["FIREBASE_PROJECT_ID", "NEXT_PUBLIC_FIREBASE"],
        "code_patterns": [r"firestore\(\)", r"collection\(", r"doc\(", r"getDocs", r"onSnapshot"],
        "warning": "Per-read ($0.06/100K), per-write ($0.18/100K). Realtime listeners multiply reads. Can spike fast.",
        "mitigation": "Cache reads. Limit realtime listeners. Use subcollections wisely. Set budget alerts.",
    },
    "vercel": {
        "name": "Vercel",
        "model": "bandwidth+functions",
        "risk_level": "medium",
        "env_keys": ["VERCEL_TOKEN", "VERCEL"],
        "code_patterns": [r"@vercel/", r"vercel\.json"],
        "warning": "Free tier: 100GB bandwidth, 100K function invocations. Overages billed per unit.",
        "mitigation": "Monitor usage dashboard. Optimize images. Use ISR/SSG where possible.",
    },
    "supabase": {
        "name": "Supabase",
        "model": "per-project+bandwidth",
        "risk_level": "low",
        "env_keys": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE"],
        "code_patterns": [r"createClient\(", r"supabase\.", r"@supabase/"],
        "warning": "Free tier: 500MB DB, 2GB bandwidth. Paid starts at $25/mo per project.",
        "mitigation": "Monitor bandwidth. Use row-level security. Set connection pool limits.",
    },
    "stripe": {
        "name": "Stripe",
        "model": "per-transaction",
        "risk_level": "medium",
        "env_keys": ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"],
        "code_patterns": [r"stripe\.", r"Stripe\(", r"checkout\.sessions"],
        "warning": "2.9% + $0.30 per transaction. Webhook failures can miss payments.",
        "mitigation": "Verify webhook signatures. Handle idempotency. Test with Stripe CLI.",
    },
    "twilio": {
        "name": "Twilio",
        "model": "per-message/call",
        "risk_level": "high",
        "env_keys": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        "code_patterns": [r"twilio\.", r"Twilio\(", r"messages\.create"],
        "warning": "SMS: $0.0079/msg US, more international. Voice: $0.013/min. Loops = disaster.",
        "mitigation": "Add rate limiting. Validate phone numbers. Set spending limits in Twilio console.",
    },
    "algolia": {
        "name": "Algolia",
        "model": "per-search+record",
        "risk_level": "medium",
        "env_keys": ["ALGOLIA_APP_ID", "ALGOLIA_API_KEY"],
        "code_patterns": [r"algoliasearch\(", r"\.search\(", r"algolia"],
        "warning": "Free: 10K searches/mo. Paid: per-search and per-record pricing. Scales fast.",
        "mitigation": "Debounce search input. Use InstantSearch query rules. Monitor search analytics.",
    },
    "google_maps": {
        "name": "Google Maps",
        "model": "per-request",
        "risk_level": "medium",
        "env_keys": ["GOOGLE_MAPS_API_KEY", "NEXT_PUBLIC_GOOGLE_MAPS"],
        "code_patterns": [r"@googlemaps", r"google\.maps", r"maps\.googleapis"],
        "warning": "$7/1K map loads, $5/1K geocoding requests. Can spike with traffic.",
        "mitigation": "Set API key restrictions. Use static maps where possible. Cache geocoding results.",
    },
    "replicate": {
        "name": "Replicate",
        "model": "per-prediction",
        "risk_level": "high",
        "env_keys": ["REPLICATE_API_TOKEN"],
        "code_patterns": [r"replicate\.run", r"replicate\.predictions"],
        "warning": "GPU-time billing. A single image generation can cost $0.01-$1+. Loops = massive bills.",
        "mitigation": "Set per-user quotas. Cache results. Add queue/rate limiter before Replicate calls.",
    },
    "pinecone": {
        "name": "Pinecone",
        "model": "per-pod/serverless",
        "risk_level": "medium",
        "env_keys": ["PINECONE_API_KEY"],
        "code_patterns": [r"pinecone\.", r"Pinecone\(", r"upsert\(", r"query\("],
        "warning": "Serverless: pay per read/write unit. Pod: $70+/mo per pod. Vector count scales cost.",
        "mitigation": "Use serverless for dev. Batch upserts. Delete unused indexes.",
    },
    "sendgrid": {
        "name": "SendGrid",
        "model": "per-email",
        "risk_level": "low",
        "env_keys": ["SENDGRID_API_KEY"],
        "code_patterns": [r"@sendgrid/mail", r"sgMail", r"sendgrid"],
        "warning": "Free: 100 emails/day. Paid starts at $19.95/mo for 50K emails.",
        "mitigation": "Use templates. Validate emails before sending. Monitor bounce rates.",
    },
    "resend": {
        "name": "Resend",
        "model": "per-email",
        "risk_level": "low",
        "env_keys": ["RESEND_API_KEY"],
        "code_patterns": [r"resend\.", r"Resend\("],
        "warning": "Free: 100 emails/day, 3K/month. $20/mo for 50K.",
        "mitigation": "Monitor usage. Use batch sending for bulk emails.",
    },
}

SCALING_TRAPS = {
    "sqlite_production": {
        "pattern": r"""(?:sqlite3|better-sqlite3|django\.db\.backends\.sqlite3|knex.*sqlite|DATABASE_URL.*sqlite)""",
        "severity": "warning",
        "message": "SQLite cannot handle concurrent writes. Will fail under production load.",
        "fix": "Use PostgreSQL, MySQL, or a managed database service for production.",
    },
    "in_memory_session": {
        "pattern": r"""(?:express-session.*?(?:MemoryStore|store:\s*undefined)|session\s*=\s*\{\})""",
        "severity": "warning",
        "message": "In-memory session store. Sessions lost on restart. Won't work with multiple instances.",
        "fix": "Use Redis, database, or JWT for session management.",
    },
    "local_file_upload": {
        "pattern": r"""(?:multer\(\s*\{[^}]*dest:\s*['"]\./|upload_to\s*=\s*['"]uploads|fs\.writeFile.*uploads)""",
        "severity": "warning",
        "message": "Files stored on local disk. Won't persist on serverless/containers. Won't scale.",
        "fix": "Use S3, Cloudinary, or a cloud storage service.",
    },
    "no_queue_for_heavy": {
        "pattern": r"""(?:(?:await|\.then).*?(?:sendEmail|processImage|generatePDF|transcode|resize))""",
        "severity": "info",
        "message": "Heavy operation (email/image/PDF) running synchronously in request handler.",
        "fix": "Use a job queue (Bull, Celery, Sidekiq) for heavy background work.",
    },
    "no_cache_layer": {
        "pattern": r"""(?:(?:app\.get|router\.get)\s*\([^)]*\)\s*(?:.*?(?:query|find|fetch)){2,})""",
        "severity": "info",
        "message": "Multiple DB queries in a single GET endpoint without caching.",
        "fix": "Add Redis/in-memory cache for frequently accessed data.",
    },
}


def detect_service_usage(root: Path) -> list[dict]:
    findings = []

    env_content = ""
    for env_name in (".env", ".env.local", ".env.production", ".env.example"):
        env_file = root / env_name
        if env_file.exists():
            try:
                env_content += env_file.read_text(encoding="utf-8", errors="ignore") + "\n"
            except (PermissionError, OSError):
                pass

    source_content = ""
    source_files = []
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
                        source_files.append((entry, content))
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

    walk(root)

    for service_id, profile in SERVICE_COST_PROFILES.items():
        detected_via = []

        for key in profile["env_keys"]:
            if key in env_content:
                detected_via.append(f"env:{key}")

        for file_path, content in source_files:
            for pat in profile["code_patterns"]:
                if re.search(pat, content, flags=re.IGNORECASE):
                    detected_via.append(f"code:{file_path.relative_to(root)}")
                    break

        if detected_via:
            findings.append({
                "type": "cost_service",
                "service": profile["name"],
                "service_id": service_id,
                "billing_model": profile["model"],
                "risk_level": profile["risk_level"],
                "detected_via": detected_via[:5],
                "severity": "warning" if profile["risk_level"] in ("high", "medium") else "info",
                "message": profile["warning"],
                "fix": profile["mitigation"],
            })

    return findings


def detect_scaling_traps(root: Path) -> list[dict]:
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
                        for trap_id, trap in SCALING_TRAPS.items():
                            if re.search(trap["pattern"], content, flags=re.IGNORECASE | re.MULTILINE):
                                findings.append({
                                    "type": "scaling_trap",
                                    "trap": trap_id,
                                    "file": str(entry.relative_to(root)),
                                    "severity": trap["severity"],
                                    "message": trap["message"],
                                    "fix": trap["fix"],
                                })
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

    walk(root)
    return findings


def run_cost_analysis(root: Path) -> dict:
    services = detect_service_usage(root)
    scaling = detect_scaling_traps(root)

    total_monthly_risk = "low"
    high_risk_count = sum(1 for s in services if s["risk_level"] == "high")
    if high_risk_count >= 2:
        total_monthly_risk = "high"
    elif high_risk_count >= 1 or len(services) >= 3:
        total_monthly_risk = "medium"

    return {
        "services": services,
        "scaling_traps": scaling,
        "total_monthly_risk": total_monthly_risk,
        "service_count": len(services),
        "high_risk_services": high_risk_count,
        "total_findings": len(services) + len(scaling),
    }
