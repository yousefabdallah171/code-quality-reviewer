# Dangerous Dependencies Reference

## Compromised / Sabotaged Packages

| Package | What Happened | Use Instead |
|---------|--------------|------------|
| `faker` (original) | Maintainer deleted code, published malicious update | `@faker-js/faker` |
| `colors` (original) | Maintainer added infinite loop | `chalk`, `picocolors` |
| `event-stream` | Supply chain attack injected crypto-stealer | Verify necessity, audit |
| `ua-parser-js` | Hijacked to mine crypto | Update to latest, verify |
| `coa` / `rc` | Hijacked with malware | Update to latest |

## Deprecated — Must Replace

| Package | Status | Replace With |
|---------|--------|-------------|
| `request` | Deprecated Feb 2020 | `node-fetch`, `undici`, native `fetch` |
| `node-sass` | Deprecated | `sass` (dart-sass) |
| `tslint` | Deprecated | `eslint` + `@typescript-eslint` |
| `istanbul` | Deprecated | `nyc` or `c8` |
| `bower` | Deprecated | npm/yarn/pnpm |
| `grunt` | Effectively abandoned | Vite, esbuild, turbopack |
| `gulp` | Declining usage | Vite, esbuild |
| `coffeescript` | Dead language | TypeScript |
| `flow-bin` | Declining | TypeScript |

## Heavy — Consider Alternatives

| Package | Size | Lighter Alternative |
|---------|------|-------------------|
| `moment` | 300KB+ | `dayjs` (2KB), `date-fns` (tree-shakeable) |
| `lodash` (full) | 70KB+ | `lodash-es` (tree-shake), individual imports |
| `jquery` | 87KB | Native DOM APIs |
| `axios` | 14KB | Native `fetch` |
| `puppeteer` | 300MB+ (Chromium) | `puppeteer-core`, `playwright` |
| `aws-sdk` v2 | 200KB+ | `@aws-sdk/client-*` v3 (modular) |
| `monaco-editor` | 500KB+ | Lazy load, `@monaco-editor/react` |
| `tensorflow` | 2GB+ | `tensorflow-lite`, `onnxruntime` |
| `torch` (PyTorch) | 2GB+ | CPU-only build if no GPU needed |

## Native Addon Risks (Deployment Issues)

| Package | Issue | Alternative |
|---------|-------|------------|
| `bcrypt` | C++ addon, compile fails on some platforms | `bcryptjs` (pure JS) |
| `sharp` | Native addon, fails on serverless | Verify platform support |
| `canvas` | Needs Cairo, complex build deps | `@napi-rs/canvas` or cloud rendering |
| `better-sqlite3` | Native, won't work on serverless | Use PostgreSQL |
| `node-gyp` deps | Require Python + C++ toolchain | Pure JS alternatives where possible |

## Security Risk Indicators

Watch for these in any dependency:
- No recent commits (abandoned)
- Single maintainer with no org backing
- Typosquatting names (e.g., `crossenv` mimicking `cross-env`)
- Unusually high permission requests
- Post-install scripts that download binaries
