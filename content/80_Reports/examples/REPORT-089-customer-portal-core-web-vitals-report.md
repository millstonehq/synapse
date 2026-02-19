---
id: REPORT-089
type: report
title: Customer Portal Core Web Vitals Report
status: approved
owner: Customer Tech Lead
created: '2025-10-28T15:45:02.790Z'
updated: '2026-08-04T14:19:03.835Z'
tags:
  - report
  - customer-portal
summary: Customer Portal Core Web Vitals Report
company: CustomerPortal
report_month: 2026-01
report_type: company
overall_health: fair
confidence: high
active_initiatives_count: 6
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Portal availability | 99.9% | 99.95% | On target |
| LCP (Largest Contentful Paint) P75 | < 2.5s | 2.1s | On target |
| FID (First Input Delay) P75 | < 100ms | 62ms | On target |
| CLS (Cumulative Layout Shift) P75 | < 0.1 | 0.08 | On target |
| Dashboard LCP P95 | < 2.0s | 1.87s | On target |
| Time to First Byte (TTFB) P75 | < 800ms | 540ms | On target |

All Core Web Vitals are in the "Good" range for January 2026. The dashboard LCP target of < 2.0s P95 was met following the server component optimization work completed in December 2025.

## Key Highlights

- **Dashboard LCP improved from 2.4s to 1.87s P95** after migrating the `DashboardSummary` GraphQL query to execute in a server component with a 2-second timeout and graceful empty-state fallback. The change reduced client-side JavaScript execution time by eliminating a client query on first load.
- **CLS reduced from 0.14 to 0.08** after adding fixed-height skeleton placeholders to the ActivityFeed and StatCards components. The remaining 0.08 CLS is caused by font loading; flagged for next sprint.
- **TTFB improved by 180ms** after enabling Vercel Edge Config for the customer session token validation, eliminating a network round-trip to the Identity Service on every server-rendered page.
- **INP baseline established**: Interaction to Next Paint (INP) was added to RUM measurement this month. Current P75 is 85ms (Good range). Target < 100ms.

## Active Initiatives

1. **Font loading CLS fix**: Implement `font-display: optional` for the portal's custom font to eliminate the 0.08 CLS from late font swap. Expected to reduce CLS to < 0.02. In progress, targeting February 2026.
2. **Image optimization audit**: 3 pages still use unoptimized `<img>` tags instead of Next.js `<Image>`. Replacing these is expected to improve LCP on those pages by 200–400ms.
3. **ActivityFeed render optimization**: ActivityFeed client component re-renders on every notification subscription event. Adding React.memo and stable key management to prevent unnecessary repaints. Expected to improve FID on dashboard pages with high notification volume.

## Incidents

No portal availability incidents in January 2026.

One performance degradation was observed on January 9, 2026 (10:15–10:42 UTC): LCP P75 rose to 3.8s for 27 minutes due to high API Gateway latency (P95 > 2s). Root cause: a database query regression in the Customer Preference Service following a migration. Resolved by reverting the migration. No SLO breach.

## Risks

No critical risks.

- **Medium**: The INP metric is at 85ms P75, within the Good range but approaching the 100ms threshold. If interactive JavaScript bundle size grows without optimization, INP could cross into the "Needs Improvement" range. Mitigation: add bundle size budget to CI (max 200kB gzipped for the main portal chunk).
- **Low**: Vercel Edge Config has a rate limit of 1000 reads/second per project. Current portal traffic is at ~300 reads/second at peak. If MAU grows 3x, this limit could be reached. Mitigation: evaluate upgrading Vercel plan before MAU reaches 80,000.

## Next Month Focus

- Resolve font loading CLS (target CLS P75 < 0.02)
- Replace 3 remaining unoptimized `<img>` tags with `<Image>`
- Implement bundle size budget in CI to prevent future LCP regression
- Publish INP baseline dashboard for ongoing monitoring
