---
id: MEETING-073
type: meeting
title: Alert Quality Improvement Session
status: review
owner: Engineering Manager
created: '2024-12-26T03:09:55.588Z'
updated: '2025-01-18T22:58:17.634Z'
tags:
  - meeting
  - monitoring-stack
summary: Alert Quality Improvement Session
company: MonitoringStack
topic: Alert Quality Improvement Session
meeting_date: '2026-10-03T11:39:31.734Z'
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

- **Project**: Monitoring Stack — Alert Quality Initiative
- **Topic**: Alert Quality Improvement Session
- **Date/Time**: 2026-10-03 11:39 AM UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Monthly alert quality review using the previous month's PagerDuty data. Focus on identifying the highest-noise alerts and agreeing on tuning actions.

## Observations by Domain

- **Alert Action Rate**: Overall alert action rate for September was 54% — below the 70% target; 8 alerts had action rates below 30%
- **P1 Alert Quality**: Three P1 alerts accounted for 42% of all pages but only 18% of actual incidents; all three are candidates for threshold increases
- **Flapping Alerts**: Two alerts are flapping (firing and resolving repeatedly within the same hour); the `for` duration needs to be increased from 1 minute to 5 minutes
- **Missing Runbooks**: 6 alerts still have no runbook URL in their annotation; on-call engineers must investigate without guidance, increasing MTTR
- **False Positive Pattern**: The `api_memory_high` alert fires during routine batch processing windows; it needs a time-of-day exception or threshold adjustment

## Key Metrics & Data Points

- **Alert action rate (September)**: 54% vs. 70% target
- **Total pages in September**: 187
- **Pages that required action**: 101 (54%)
- **Alerts with action rate below 30%**: 8 alerts
- **Mean MTTA (September)**: 8.3 minutes (target: 5 minutes)
- **Mean MTTR (September)**: 34 minutes (target: 25 minutes)

## Preliminary Scorecard Hooks

- Alert Action Rate: 2/5 - 54% is significantly below the 70% target
- Runbook Coverage: 2/5 - 6 critical alerts still missing runbooks
- Flapping Control: 3/5 - 2 actively flapping alerts identified; `for` duration fixes are straightforward
- P1 Quality: 2/5 - 3 P1 alerts with very low action rates are damaging on-call experience
- Process Adherence: 3/5 - Monthly review cadence is being followed; tuning backlog is growing

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Alert fatigue leads to on-call engineer ignoring real incidents | High | Medium | Engineering Manager | Prioritize P1 alert tuning this sprint; measure MTTA weekly | 2026-10-17 |
| Threshold increases cause real incidents to go undetected | Medium | Low | Tech Lead | Validate new thresholds against historical incident data before deploying | 2026-10-24 |
| Alert tuning backlog grows faster than team can address | Medium | Medium | Principal Engineer | Establish alert debt budget: max 5 alerts in the "needs tuning" backlog at any time | 2026-11-01 |

## Decisions & Next Steps

### Decisions

- Raise `for` duration to 5 minutes for all alerts currently at 1 minute; exceptions require documented justification
- No new P1 alert may be deployed without a runbook URL in the alert annotation
- The 8 lowest-action-rate alerts will be addressed this sprint before any new alerts are added

### Action Items

- Tech Lead to raise `for` duration on the two flapping alerts (due 2026-10-10)
- Principal Engineer to audit and write runbooks for the 6 alerts missing runbook links (due 2026-10-17)
- QA Lead to retest the `api_memory_high` alert threshold using September's historical data (due 2026-10-17)

### Follow-ups

- Review September alert action rate trend at next monthly meeting
- Schedule on-call experience retrospective for end of October with all rotation participants
