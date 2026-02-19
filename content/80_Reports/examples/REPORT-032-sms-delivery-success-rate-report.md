---
id: REPORT-032
type: report
title: SMS Delivery Success Rate Report
status: approved
owner: Notification Tech Lead
created: '2025-04-18T05:00:06.472Z'
updated: '2025-06-09T14:23:14.569Z'
tags:
  - report
  - notification-service
summary: SMS Delivery Success Rate Report
company: NotificationService
report_month: 2026-11
report_type: analytics
overall_health: poor
confidence: medium
active_initiatives_count: 1
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall SMS delivery success | > 97% | 94.1% | Below target |
| Transactional SMS success | > 99% | 98.7% | On target |
| Marketing SMS success | > 95% | 90.8% | Below target |
| Carrier opt-out compliance | 100% | 100% | On target |
| Provider acceptance rate | > 99% | 98.4% | On target |

Overall SMS delivery success has fallen below the 97% target, driven by poor marketing SMS performance. Investigation revealed that a significant portion of marketing SMS failures are attributable to carrier-level filtering of messages that match spam patterns in our promotional copy. Transactional SMS performance remains strong.

## Key Highlights

- **Carrier filtering identified as root cause**: 68% of marketing SMS failures in the past 30 days resulted in a `30007` (carrier violation) or `30008` (unknown carrier error) error from Twilio, indicating carrier-level spam filtering rather than provider or gateway issues.
- **Copy review process initiated**: Working with the content team to review marketing SMS templates against carrier content guidelines. Initial audit found 4 templates with high spam-signal patterns.
- **STOP compliance at 100%**: All opt-out registrations are being honored within the required timeframe. No compliance findings.

## Active Initiatives

1. **Marketing SMS template audit and remediation**: Content team reviewing all 34 active marketing SMS templates against carrier guidelines. Timeline: 2 weeks.

## Incidents

No SMS delivery incidents this period. The poor performance is a gradual degradation, not an acute incident.

## Risks

- **High**: If carrier filtering continues at current rates, marketing SMS success rate may decline further. Risk of carrier blacklisting if spam signals accumulate.

## Next Month Focus

- Complete marketing SMS template audit and remediate flagged templates
- Implement automated carrier guideline checking in the template approval workflow
- Evaluate A2P 10DLC registration status for all sending numbers
- Monitor delivery rates after template remediations to confirm recovery
