---
id: STANDARD-051
type: standard
title: Customer Portal Performance Standard
status: approved
owner: Security Lead
created: '2025-09-18T19:31:30.586Z'
updated: '2026-02-03T01:22:01.296Z'
tags:
  - standard
  - customer-portal
summary: Customer Portal Performance Standard
related_policies:
  - POLICY-044
  - POLICY-041
example: true
related_systems:
  - SYSTEM-043
  - SYSTEM-044
---

## Area

This standard defines the performance targets and measurement requirements for the Customer Portal. It covers initial page load performance, runtime interaction responsiveness, API latency budgets, and asset delivery. All frontend features and backend API endpoints serving portal traffic must be developed and tested against these targets before shipping to production.

## Controls

- Initial page load Largest Contentful Paint (LCP) must be under 2.5 seconds on a simulated 4G connection in Lighthouse
- Cumulative Layout Shift (CLS) must remain below 0.1 across all portal pages
- Time to First Byte (TTFB) for authenticated API endpoints must be under 200ms at P50 and under 800ms at P95 under normal load
- JavaScript bundle size for the initial route must not exceed 250KB gzipped; new dependencies must be evaluated for bundle impact before merging
- Images and media assets must be served in modern formats (WebP/AVIF) with appropriate responsive sizes; no unoptimized images above 100KB
- Performance regression tests must run in CI; merges that degrade Lighthouse performance score by more than 5 points require explicit review approval

## Compliance Mappings

- Core Web Vitals (Google): LCP, CLS, and INP targets align with "Good" threshold definitions
- WCAG 2.1 SC 2.2.1: Timing adjustable - fast load times reduce dependency on timing-sensitive interactions
- Internal [[POLICY-044|Customer Content Moderation Policy]] (rendered UGC must not degrade page performance)

## Related Policies

- [[POLICY-044|Customer Content Moderation Policy]]
- [[POLICY-041|Customer Data Privacy Policy]]
