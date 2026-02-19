---
id: MEETING-083
type: meeting
title: Customer Portal Performance Review
status: accepted
owner: Engineering Manager
created: '2024-05-31T20:06:57.177Z'
updated: '2025-10-28T08:16:26.153Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Performance Review
company: CustomerPortal
topic: Customer Portal Performance Review
meeting_date: '2026-01-16T23:08:36.059Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Customer Portal Platform
- **Topic**: Monthly Performance Review - Core Web Vitals and API Latency Trends
- **Date/Time**: 2026-01-16 3:00 PM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Monthly review of portal performance metrics against the Customer Portal Performance Standard targets. Reviewing trends since the December release.

## Observations by Domain

- **Core Web Vitals**: LCP is at 2.1s median (target: under 2.5s) but has trended up 0.3s over the past 6 weeks; the trend is concerning even though the threshold is not yet breached
- **API Latency**: P95 API latency is at 740ms, up from 680ms last month; the `/accounts/{id}/activity` endpoint is the primary outlier at 1.1s P95
- **Bundle Size**: Initial bundle is at 241KB gzipped, approaching the 250KB limit; the recent addition of a date picker library contributed 18KB
- **CDN Performance**: Cache hit ratio is stable at 89%; no anomalies noted
- **Real User Monitoring**: Field data from RUM shows 12% of users experiencing LCP above 4s, concentrated in APAC regions where CDN edge coverage is thinner

## Key Metrics & Data Points

- **LCP (lab)**: 2.1s median, up from 1.8s six weeks ago
- **LCP (field, APAC)**: 4.2s at P75 — significantly above target
- **API P95 latency**: 740ms overall; 1.1s for `/accounts/{id}/activity`
- **Initial JS bundle**: 241KB gzipped (target: <250KB)
- **CDN cache hit ratio**: 89% (stable, target: >85%)

## Preliminary Scorecard Hooks

- LCP Performance: 3/5 - Meeting lab target but trending up and APAC field data is poor
- API Latency: 3/5 - Within target overall but one endpoint is significantly above threshold
- Bundle Management: 3/5 - Approaching limit; date picker addition was not scrutinized
- CDN Efficiency: 4/5 - Cache hit ratio is healthy and stable
- Geographic Coverage: 2/5 - APAC performance significantly lags other regions

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| LCP trend breaches target before fix is deployed | High | Medium | Tech Lead | Identify LCP regression cause and deploy fix in next sprint | 2026-02-01 |
| Activity endpoint latency triggers SLA breach | High | Medium | Principal Engineer | Add database query optimization and caching for activity endpoint | 2026-01-30 |
| Bundle exceeds 250KB limit in next sprint | Medium | High | Tech Lead | Enforce bundle review for all new dependency additions; replace date picker | 2026-02-15 |
| APAC LCP degraded user experience | Medium | High | Principal Engineer | Evaluate adding CloudFront edge locations in APAC | 2026-02-28 |

## Decisions & Next Steps

### Decisions

- The `/accounts/{id}/activity` endpoint investigation is escalated to P1 engineering; query execution plan analysis to happen this sprint
- All new dependency additions over 5KB must include a bundle analyzer screenshot in the PR description
- APAC CDN coverage evaluation to be added to Q1 infrastructure roadmap

### Action Items

- Principal Engineer to profile activity endpoint query and propose optimization (due 2026-01-23)
- Tech Lead to identify cause of LCP regression using Lighthouse CI report comparison (due 2026-01-20)
- Engineering Manager to initiate APAC CDN expansion evaluation with infrastructure team (due 2026-02-01)

### Follow-ups

- Next performance review scheduled for 2026-02-13
- Activity endpoint fix to be validated against P95 target before next review
