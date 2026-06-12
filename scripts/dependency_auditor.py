"""Dependency auditing — heavy packages, deprecated libs, risk scoring."""

from __future__ import annotations

HEAVY_JS_PACKAGES = {
    "moment": {"reason": "Massive bundle size (300KB+). Use date-fns or dayjs instead.", "severity": "warning"},
    "lodash": {"reason": "Full lodash is 70KB+. Use lodash-es or individual imports (lodash/get).", "severity": "warning"},
    "underscore": {"reason": "Outdated utility lib. Modern JS covers most use cases.", "severity": "info"},
    "jquery": {"reason": "Heavy DOM library (87KB). Modern frameworks don't need it.", "severity": "warning"},
    "axios": {"reason": "Consider native fetch. Axios adds 14KB for what fetch does natively.", "severity": "info"},
    "request": {"reason": "Deprecated since 2020. Use node-fetch, undici, or native fetch.", "severity": "critical"},
    "faker": {"reason": "Original faker was compromised. Use @faker-js/faker instead.", "severity": "critical"},
    "colors": {"reason": "Was sabotaged by its maintainer. Use chalk or picocolors.", "severity": "critical"},
    "event-stream": {"reason": "Had a supply chain attack. Verify you need this.", "severity": "critical"},
    "node-sass": {"reason": "Deprecated. Use sass (dart-sass) instead.", "severity": "warning"},
    "tslint": {"reason": "Deprecated. Use eslint with @typescript-eslint.", "severity": "warning"},
    "puppeteer": {"reason": "Downloads Chromium (300MB+). Use playwright or puppeteer-core.", "severity": "info"},
    "bcrypt": {"reason": "Native C++ addon causes install issues. Consider bcryptjs for pure JS.", "severity": "info"},
    "sharp": {"reason": "Native addon — may cause deployment issues on serverless. Verify compatibility.", "severity": "info"},
    "canvas": {"reason": "Native addon with complex build deps. Consider alternatives for serverless.", "severity": "info"},
}

HEAVY_PYTHON_PACKAGES = {
    "pandas": {"reason": "Large dependency. If only doing simple CSV, consider csv module.", "severity": "info"},
    "tensorflow": {"reason": "Very large (500MB+). Consider tensorflow-lite or onnxruntime if possible.", "severity": "info"},
    "torch": {"reason": "Very large (2GB+). Pin to CPU-only if no GPU needed.", "severity": "info"},
    "opencv-python": {"reason": "Large binary. Use opencv-python-headless for servers.", "severity": "info"},
    "boto3": {"reason": "AWS SDK — pay-as-you-go service. Monitor usage and set billing alerts.", "severity": "warning"},
    "flask-cors": {"reason": "Review CORS config. Default allow-all is a security risk.", "severity": "warning"},
}

DEPRECATED_PACKAGES = {
    "request": "Deprecated since 2020",
    "tslint": "Deprecated — use eslint",
    "node-sass": "Deprecated — use dart-sass",
    "istanbul": "Deprecated — use nyc or c8",
    "mocha": "Consider vitest or jest for modern projects",
    "bower": "Deprecated — use npm/yarn",
    "grunt": "Consider modern bundlers (vite, esbuild)",
    "gulp": "Consider modern bundlers (vite, esbuild)",
    "coffeescript": "Deprecated language — migrate to TypeScript",
    "flow-bin": "Consider TypeScript instead",
}

PAY_AS_YOU_GO_SDKS = {
    "openai": {"service": "OpenAI API", "risk": "Token-based billing. Unbounded calls can spike costs.", "severity": "warning"},
    "@anthropic-ai/sdk": {"service": "Anthropic API", "risk": "Token-based billing. Monitor usage.", "severity": "warning"},
    "anthropic": {"service": "Anthropic API", "risk": "Token-based billing. Monitor usage.", "severity": "warning"},
    "stripe": {"service": "Stripe", "risk": "Transaction fees. Verify webhook security.", "severity": "info"},
    "@stripe/stripe-js": {"service": "Stripe", "risk": "Transaction fees. Verify webhook security.", "severity": "info"},
    "aws-sdk": {"service": "AWS", "risk": "Pay-as-you-go. Set billing alerts and usage limits.", "severity": "warning"},
    "@aws-sdk/client-s3": {"service": "AWS S3", "risk": "Storage + transfer costs. Set lifecycle policies.", "severity": "warning"},
    "@aws-sdk/client-ses": {"service": "AWS SES", "risk": "Per-email pricing. Add rate limiting.", "severity": "warning"},
    "@aws-sdk/client-lambda": {"service": "AWS Lambda", "risk": "Per-invocation billing. Watch cold starts.", "severity": "warning"},
    "boto3": {"service": "AWS", "risk": "Pay-as-you-go. Set billing alerts.", "severity": "warning"},
    "google-cloud-storage": {"service": "GCP Storage", "risk": "Storage + egress costs.", "severity": "warning"},
    "google-cloud-bigquery": {"service": "BigQuery", "risk": "Per-query billing on data scanned. Use partitioning.", "severity": "warning"},
    "@google-cloud/storage": {"service": "GCP Storage", "risk": "Storage + egress costs.", "severity": "warning"},
    "firebase": {"service": "Firebase", "risk": "Read/write quotas. Firestore can spike costs.", "severity": "warning"},
    "firebase-admin": {"service": "Firebase Admin", "risk": "Backend access to Firebase. Monitor Firestore reads.", "severity": "warning"},
    "twilio": {"service": "Twilio", "risk": "Per-message/call pricing. Add rate limiting.", "severity": "warning"},
    "sendgrid": {"service": "SendGrid", "risk": "Per-email pricing at scale.", "severity": "info"},
    "@sendgrid/mail": {"service": "SendGrid", "risk": "Per-email pricing at scale.", "severity": "info"},
    "resend": {"service": "Resend", "risk": "Per-email pricing. Free tier is limited.", "severity": "info"},
    "pusher": {"service": "Pusher", "risk": "Per-connection and per-message pricing.", "severity": "warning"},
    "algolia": {"service": "Algolia", "risk": "Per-search and per-record pricing. Can be expensive.", "severity": "warning"},
    "algoliasearch": {"service": "Algolia", "risk": "Per-search and per-record pricing.", "severity": "warning"},
    "supabase": {"service": "Supabase", "risk": "Free tier limits. Paid plan is per-project.", "severity": "info"},
    "@supabase/supabase-js": {"service": "Supabase", "risk": "Free tier limits on bandwidth and storage.", "severity": "info"},
    "pinecone-client": {"service": "Pinecone", "risk": "Vector DB pricing per pod/serverless. Can spike.", "severity": "warning"},
    "@pinecone-database/pinecone": {"service": "Pinecone", "risk": "Vector DB pricing.", "severity": "warning"},
    "replicate": {"service": "Replicate", "risk": "Per-prediction GPU billing. Very expensive at scale.", "severity": "warning"},
    "together": {"service": "Together AI", "risk": "Per-token billing for AI inference.", "severity": "warning"},
    "cloudinary": {"service": "Cloudinary", "risk": "Per-transformation and bandwidth pricing.", "severity": "info"},
    "uploadthing": {"service": "Uploadthing", "risk": "Storage and bandwidth costs at scale.", "severity": "info"},
}

DUPLICATE_FUNCTIONALITY = [
    (["axios", "node-fetch", "got", "undici", "ky", "superagent"], "HTTP client — pick one"),
    (["moment", "dayjs", "date-fns", "luxon"], "Date library — pick one"),
    (["lodash", "underscore", "ramda"], "Utility library — pick one"),
    (["jest", "vitest", "mocha", "ava", "tap"], "Test runner — pick one"),
    (["eslint", "tslint", "biome"], "Linter — pick one"),
    (["prettier", "biome"], "Formatter — pick one unless biome covers both"),
    (["styled-components", "emotion", "@emotion/react", "tailwindcss"], "CSS approach — avoid mixing"),
    (["zustand", "redux", "@reduxjs/toolkit", "jotai", "recoil", "mobx", "valtio"], "State management — pick one"),
    (["express", "fastify", "koa", "hapi"], "HTTP server — pick one"),
    (["winston", "pino", "bunyan", "morgan"], "Logger — pick one"),
    (["bcrypt", "bcryptjs", "argon2"], "Password hashing — pick one (prefer argon2)"),
    (["passport", "next-auth", "clerk", "auth0", "lucia"], "Auth — pick one"),
]


def audit_dependencies(stack: dict) -> dict:
    all_deps = stack.get("all_deps", {})
    js_deps = stack.get("js_deps", {})
    py_deps = stack.get("py_deps", [])
    findings = []

    for dep_name in all_deps:
        dep_lower = dep_name.lower()
        if dep_lower in HEAVY_JS_PACKAGES:
            info = HEAVY_JS_PACKAGES[dep_lower]
            findings.append({
                "type": "heavy_dependency",
                "package": dep_name,
                "severity": info["severity"],
                "message": info["reason"],
            })
        if dep_lower in HEAVY_PYTHON_PACKAGES:
            info = HEAVY_PYTHON_PACKAGES[dep_lower]
            findings.append({
                "type": "heavy_dependency",
                "package": dep_name,
                "severity": info["severity"],
                "message": info["reason"],
            })

    for dep_name in all_deps:
        dep_lower = dep_name.lower()
        if dep_lower in DEPRECATED_PACKAGES:
            findings.append({
                "type": "deprecated",
                "package": dep_name,
                "severity": "warning",
                "message": DEPRECATED_PACKAGES[dep_lower],
            })

    for dep_name in all_deps:
        dep_lower = dep_name.lower()
        if dep_lower in PAY_AS_YOU_GO_SDKS:
            info = PAY_AS_YOU_GO_SDKS[dep_lower]
            findings.append({
                "type": "cost_risk",
                "package": dep_name,
                "service": info["service"],
                "severity": info["severity"],
                "message": info["risk"],
            })

    dep_set = set(d.lower() for d in all_deps)
    for group, description in DUPLICATE_FUNCTIONALITY:
        matches = [g for g in group if g.lower() in dep_set]
        if len(matches) > 1:
            findings.append({
                "type": "duplicate_functionality",
                "packages": matches,
                "severity": "info",
                "message": f"{description}. Found: {', '.join(matches)}",
            })

    return {
        "findings": findings,
        "total_deps": len(all_deps),
        "heavy_count": sum(1 for f in findings if f["type"] == "heavy_dependency"),
        "deprecated_count": sum(1 for f in findings if f["type"] == "deprecated"),
        "cost_risk_count": sum(1 for f in findings if f["type"] == "cost_risk"),
        "duplicate_count": sum(1 for f in findings if f["type"] == "duplicate_functionality"),
    }
