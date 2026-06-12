# Cost & Risk Catalog

## Pay-As-You-Go Services — Pricing Guide

### AI / LLM APIs (HIGHEST RISK)

| Service | Pricing Model | Typical Cost | Danger Zone |
|---------|--------------|-------------|-------------|
| OpenAI GPT-4 | Per token | $30-60/M tokens | Unbounded loops, no caching |
| OpenAI GPT-3.5 | Per token | $0.50-1.50/M tokens | Still adds up without limits |
| Anthropic Claude | Per token | $3-75/M tokens | Long context windows multiply cost |
| Replicate | Per prediction (GPU time) | $0.01-$5/prediction | Image generation loops |
| ElevenLabs | Per character | $0.30/1K chars | Long text synthesis |
| Google AI (Gemini) | Per token | $1.25-5/M tokens | Similar to OpenAI risks |

**Mitigation**: Always set spending limits. Cache responses. Use cheaper models for simple tasks. Rate limit per user.

### Cloud Storage

| Service | Pricing Model | Typical Cost | Danger Zone |
|---------|--------------|-------------|-------------|
| AWS S3 | Storage + transfer | $0.023/GB/mo + $0.09/GB out | Large files, no lifecycle |
| GCP Storage | Storage + transfer | $0.020/GB/mo + $0.12/GB out | Egress costs hidden |
| Cloudinary | Transformations + bandwidth | $0.015/transform | On-the-fly transforms in loops |
| Vercel Blob | Storage + bandwidth | $0.15/GB stored | Large file uploads |

### Databases

| Service | Pricing Model | Typical Cost | Danger Zone |
|---------|--------------|-------------|-------------|
| Supabase | Per project + bandwidth | $25/mo/project | Multiple projects |
| PlanetScale | Per reads/writes | $29/mo + $1.50/B reads | N+1 queries |
| Firebase Firestore | Per read/write | $0.06/100K reads | Realtime listeners |
| MongoDB Atlas | Per cluster | $57+/mo dedicated | Auto-scaling without limits |
| Neon | Per compute hour | $0.16/compute-hr | Always-on connections |

### Communication

| Service | Pricing Model | Typical Cost | Danger Zone |
|---------|--------------|-------------|-------------|
| Twilio SMS | Per message | $0.0079/msg (US) | Notification loops |
| SendGrid | Per email | $19.95/50K emails | Bulk email without queue |
| Resend | Per email | $20/50K emails | Same as above |
| Pusher | Per connection + message | $49/mo for 500 connections | Realtime at scale |

### Search

| Service | Pricing Model | Typical Cost | Danger Zone |
|---------|--------------|-------------|-------------|
| Algolia | Per search + record | $1/1K searches | No debounce on input |
| Pinecone | Per pod / serverless | $70+/mo per pod | Growing vector count |
| ElasticSearch (cloud) | Per node | $95+/mo | Data volume growth |

## Scaling Traps

### SQLite in Production
- **Problem**: Single writer, no concurrent writes, file-based
- **Symptom**: "database is locked" errors under load
- **Fix**: PostgreSQL or MySQL for any multi-user production app
- **Exception**: Embedded/single-user apps, read-heavy analytics

### In-Memory Sessions
- **Problem**: Sessions lost on restart, can't scale horizontally
- **Symptom**: Users randomly logged out, sessions lost on deploy
- **Fix**: Redis session store or JWT tokens

### Local File Storage
- **Problem**: Files lost on redeploy (serverless/containers), can't scale
- **Symptom**: Uploads disappear, 404 on previously uploaded files
- **Fix**: S3, Cloudinary, or Vercel Blob

### No Connection Pooling
- **Problem**: Each request creates new DB connection, exhausts limit
- **Symptom**: "too many connections" errors under moderate load
- **Fix**: Use connection pool (pg.Pool, mysql.createPool, SQLAlchemy pool)

### Synchronous Heavy Operations
- **Problem**: Blocks request handler, causes timeouts
- **Symptom**: Slow responses, 504 Gateway Timeout
- **Fix**: Background job queue (Bull, Celery, Sidekiq)

### No Rate Limiting
- **Problem**: Single user/bot can exhaust API quotas or DB capacity
- **Symptom**: Unexpected bills, service degradation
- **Fix**: Add rate limiting to all external-facing endpoints

### Missing Caching
- **Problem**: Same expensive queries/API calls repeated every request
- **Symptom**: Slow responses, high DB/API costs
- **Fix**: Redis cache, HTTP cache headers, in-memory cache for hot data

## Cost Monitoring Checklist

- [ ] Billing alerts set on all cloud services
- [ ] Monthly spending caps configured where possible
- [ ] Rate limiting on all AI/LLM API calls
- [ ] Caching layer for repeated expensive operations
- [ ] Database connection pooling configured
- [ ] Image optimization pipeline in place
- [ ] CDN for static asset delivery
- [ ] Queue system for heavy background work
- [ ] Monitoring dashboard for service usage
