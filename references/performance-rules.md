# Performance Rules Reference

## Database Performance

### N+1 Query Problem
```
BAD:  for user in users: user.posts = db.query(posts, user_id=user.id)
GOOD: posts = db.query(posts, user_id__in=[u.id for u in users])
```
- Use eager loading / includes / joins
- Batch queries outside loops
- Use `.select_related()` / `.prefetch_related()` (Django)
- Use `.include()` (Prisma)
- Use `.preload()` / `.eager_load()` (Rails)

### Missing Pagination
- NEVER return all records: always `.limit()` / `.take()` / `.paginate()`
- Use cursor-based pagination for large datasets
- Default page size: 20-50 items

### Connection Pooling
- NEVER use `mysql.createConnection()` — use `mysql.createPool()`
- NEVER use `pg.Client` directly — use `pg.Pool`
- Set max connections based on environment (5 dev, 20-50 prod)

### Indexing
- Add indexes to columns used in WHERE, JOIN, ORDER BY
- Composite indexes for multi-column queries
- Don't over-index — each index slows writes

## Frontend Performance

### Bundle Size
- Tree-shake: import `{ specific }` not `import *`
- Lazy load: `React.lazy()`, `next/dynamic`, dynamic `import()`
- Analyze: `npx webpack-bundle-analyzer` or `npx vite-bundle-visualizer`
- Target: < 200KB initial JS (gzipped)

### Images
- Use WebP/AVIF over PNG/JPEG (30-50% smaller)
- Use `<Image>` components (Next.js, Nuxt) for auto-optimization
- Lazy load below-fold images
- Set explicit width/height to prevent layout shift
- Max image size: 200KB for hero, 50KB for thumbnails

### Rendering
- Minimize re-renders: `React.memo`, `useMemo`, `useCallback`
- Avoid inline objects/arrays in JSX props
- Use virtualization for long lists (`react-window`, `tanstack-virtual`)
- Don't put expensive computation in render path

### Network
- Enable gzip/brotli compression
- Set cache headers for static assets
- Use CDN for static files
- Prefetch critical resources
- Minimize third-party scripts

## API Performance

### Response Time Targets
- P50: < 100ms
- P95: < 500ms
- P99: < 1s
- Anything > 2s: needs investigation or background processing

### Rate Limiting
- Auth endpoints: 5-10 requests/minute per IP
- API endpoints: 100-1000 requests/minute per user
- Webhooks: queue and process async
- AI API calls: always rate limit, always cache

### Caching Strategy
- Static data: cache aggressively (hours/days)
- User-specific data: cache with user key (minutes)
- Frequently computed data: Redis/in-memory cache
- API responses: HTTP cache headers

## Background Processing

### When to Use Queues
- Email sending
- Image/video processing
- PDF generation
- AI/ML inference
- Data imports/exports
- Webhook delivery
- Report generation

### Queue Best Practices
- Use Bull/BullMQ (Node), Celery (Python), Sidekiq (Ruby)
- Set max retries and exponential backoff
- Add dead letter queue for failed jobs
- Monitor queue depth and processing time

## Mobile / Reduced Motion

- Disable parallax on touch devices
- Disable pinned sections on mobile
- Reduce animation durations on mobile
- Respect `prefers-reduced-motion` media query
- Test on real devices, not just devtools emulation
