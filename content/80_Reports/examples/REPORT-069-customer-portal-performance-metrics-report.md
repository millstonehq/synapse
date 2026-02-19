---
id: REPORT-069
type: report
title: Customer Portal Performance Metrics Report
status: review
owner: Customer Tech Lead
created: '2024-12-16T01:26:24.752Z'
updated: '2025-05-28T00:42:23.428Z'
tags:
  - report
  - customer-portal
summary: Customer Portal Performance Metrics Report
company: CustomerPortal
report_month: 2026-03
report_type: company
overall_health: poor
confidence: medium
active_initiatives_count: 7
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Availability | 99.95% | 99.93% | Slightly below |
| P50 page load | < 1s | 730ms | On target |
| P95 page load | < 2.5s | 2.1s | On target |
| P95 GraphQL response | < 300ms | 258ms | On target |
| P99 GraphQL response | < 1s | 940ms | On target |
| CDN cache hit rate | > 80% | 83% | On target |

Performance metrics are largely healthy. Availability dipped slightly below target due to a 3-hour window of elevated error rates caused by a database connection pool misconfiguration that was corrected without a full outage.

## Key Highlights

- **GraphQL query optimization**: Three slow resolvers in the dashboard page query were identified and optimized. P95 GraphQL response dropped from 380ms to 258ms following the changes.
- **CDN cache hit rate improved**: Tuning of cache-control headers for preference API responses and static page metadata pushed cache hit rate from 74% to 83%.
- **Image optimization**: WebP conversion enabled for all portal images via Next.js Image component. Average image payload per page reduced by 41%.

## Active Initiatives

1. **Core Web Vitals improvement program**: LCP and CLS are both below Google's "Good" thresholds for approximately 15% of sessions. Investigation underway.
2. **GraphQL persisted queries**: Adopting persisted query IDs in production to reduce payload and prevent ad-hoc queries. Rollout planned next month.
3. **Server-side caching layer**: Evaluating Redis response caching at the API Gateway level for high-traffic, low-variability queries.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| No SEV incidents | - | - | - |

No SEV-1 or SEV-2 incidents this period.

## Risks

- **Medium**: Core Web Vitals LCP degradation primarily affects mobile users on slow connections. May require server component restructuring to resolve.
- **Low**: GraphQL persisted query rollout requires client and server changes to be coordinated; partial rollout could cause cache misses.

## Next Month Focus

- Diagnose and fix Core Web Vitals LCP issue on mobile
- Ship GraphQL persisted queries to production
- Begin server-side caching layer prototype
- Re-evaluate P99 GraphQL response target (940ms is close to 1s threshold)
