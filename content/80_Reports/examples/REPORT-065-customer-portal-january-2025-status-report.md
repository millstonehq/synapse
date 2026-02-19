---
id: REPORT-065
type: report
title: Customer Portal January 2025 Status Report
status: approved
owner: Customer Tech Lead
created: '2025-01-12T09:08:22.057Z'
updated: '2026-04-03T16:29:31.386Z'
tags:
  - report
  - customer-portal
summary: Customer Portal January 2025 Status Report
company: CustomerPortal
report_month: 2024-02
report_type: company
overall_health: poor
confidence: high
active_initiatives_count: 7
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Availability | 99.95% | 99.96% | On target |
| P50 page load | < 1s | 780ms | On target |
| P95 API response | < 300ms | 241ms | On target |
| Error rate | < 0.5% | 0.12% | On target |
| Support ticket CSAT | > 4.0 / 5.0 | 4.2 | On target |
| Active users (DAU) | 12,000 | 11,840 | Near target |

January showed stable performance across all SLAs. A brief CDN misconfiguration on Jan 9 caused elevated 404 rates for static assets for approximately 18 minutes but was resolved without escalation.

## Key Highlights

- **Notification center beta shipped**: The new in-app notification center launched to 20% of users on Jan 14. Early engagement shows 38% of users reading notifications within 1 hour of delivery.
- **Login page redesign**: Updated login flow with improved error messaging and password reset UX went fully live Jan 7. Password reset completion rate improved from 61% to 79%.
- **Support widget stability**: The Customer Support Widget Service maintained 100% availability in January after the Redis session store was scaled up in December.

## Active Initiatives

1. **Notification center GA rollout** (70% → 100%): Targeting full rollout by Feb 7. No blockers identified.
2. **Dashboard redesign**: Design review completed. Engineering kickoff scheduled for Feb 3.
3. **Accessibility remediation**: WCAG 2.2 audit findings from December are being worked down. 14 of 22 issues resolved.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Jan 9 | SEV-3 | 18 min | CDN misconfiguration caused 404s for static assets. Resolved by reverting CDN cache rule. |

No SEV-1 or SEV-2 incidents in January.

## Risks

- **Medium**: Dashboard redesign introduces new GraphQL queries; performance impact in production not yet validated. Mitigation: load test against staging before rollout.
- **Low**: Notification center email fallback not yet implemented. Users without portal sessions miss notifications.

## Next Month Focus

- Complete notification center GA rollout
- Begin dashboard redesign engineering sprint
- Close remaining 8 accessibility remediation items
- Conduct Q1 performance baseline measurement
