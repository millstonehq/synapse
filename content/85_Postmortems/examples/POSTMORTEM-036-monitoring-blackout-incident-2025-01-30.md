---
id: POSTMORTEM-036
type: postmortem
title: Monitoring Blackout Incident 2025-01-30
status: approved
owner: Incident Commander
created: '2024-02-04T07:05:15.265Z'
updated: '2026-12-11T01:32:55.647Z'
tags:
  - postmortem
  - monitoring-stack
summary: Monitoring Blackout Incident 2025-01-30
incident_number: INC-737
severity: SEV-1
incident_date: '2024-12-29'
detection_time: '2025-01-08T14:11:06.388Z'
resolution_time: '2024-03-01T11:55:32.391Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-072
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 30, 2025, the monitoring platform experienced a complete 2-hour blackout when Prometheus ran out of local disk space during a TSDB compaction cycle. With metrics ingestion stopped, all dashboards went dark, alert evaluation halted, and on-call engineers lost visibility into the health of all production services. No application services were affected, but the monitoring blind spot created significant operational risk. The root cause was unmonitored disk growth in the Prometheus TSDB combined with a compaction cycle that generated temporary disk usage exceeding available capacity.

Detection was delayed by the nature of the failure: the monitoring system was down, so it could not alert on its own failure. An engineer noticed the dark dashboards while reviewing a routine deployment and raised the incident manually at 14:50 UTC.

## Timeline

- **12:30** - Prometheus TSDB compaction cycle begins (scheduled, 2-hour cycle)
- **13:45** - Prometheus disk utilization crosses 90% as compaction generates temporary duplicate block files
- **14:20** - Prometheus disk reaches 100%; scrape loop pauses. No alert fires (alerting is down)
- **14:50** - Engineer notices all Grafana dashboards are empty while reviewing a deploy; manually raises incident INC-737
- **14:55** - On-call engineer confirms both Prometheus HA instances are in disk-full state
- **15:05** - Deleted oldest TSDB blocks (7-day data) to free 80GB; Prometheus resumes scraping
- **15:20** - Metrics ingestion restored; dashboards return to normal. 2-hour gap in all metric history
- **16:30** - Incident closed; postmortem scheduled

## Impact

- **Duration**: 2 hours (14:20 - 16:30 UTC) of monitoring blackout
- **Users affected**: All engineering teams — no production visibility during the window
- **Metric data loss**: 2-hour gap in all time-series data (Jan 30 14:20-16:30 UTC)
- **Alert suppression**: All alerting halted for 2 hours — no SEV-1/SEV-2 alerts could fire
- **Operational risk**: Any production incident occurring during the blackout window would have been invisible to on-call engineers

## Root Cause Analysis

1. **Unmonitored Prometheus disk growth**: Prometheus TSDB disk usage grew from 60% to 94% over 6 weeks as metric cardinality increased with new service onboarding. No disk utilization alert existed for the Prometheus pods themselves (a monitoring gap in the self-monitoring configuration).

2. **Compaction amplification**: TSDB compaction creates temporary copies of blocks before deleting originals. Peak disk usage during compaction can reach 150-200% of steady-state. The available headroom (6% = ~30GB) was insufficient for the compaction working set (~80GB required).

## Resolution

1. Manually deleted the oldest 7 days of TSDB blocks to free 80GB of space
2. Prometheus restarted and resumed scraping
3. Remote write caught up with 2-hour backfill from the persistent queue (WAL replay)
4. Disk capacity expansion planned and prioritized for February

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add Prometheus disk usage alert at 70% (warn) and 85% (critical) | SRE | P1 | 2025-02-03 | Completed |
| Expand Prometheus TSDB volume from 500GB to 1TB | Infra | P1 | 2025-02-14 | Completed |
| Set remote write persistent queue (WAL-backed) | Monitoring Eng | P1 | 2025-02-28 | Completed |
| Reduce TSDB local retention from 15d to 10d | Monitoring Eng | P2 | 2025-02-14 | Completed |
| Add self-monitoring runbook section to Prometheus runbook | On-call | P2 | 2025-02-07 | Completed |
| Document compaction disk amplification factor in capacity planning guide | Monitoring Eng | P3 | 2025-03-01 | Completed |

## Lessons Learned

- **What went well**: The engineer who spotted the dark dashboards escalated quickly. Once the root cause was identified (disk full), resolution was straightforward and fast.
- **What went poorly**: Detection relied on human observation rather than automated alerting. The monitoring system had no self-monitoring for its own disk health. The 2-hour blackout window was entirely avoidable.
- **What was lucky**: No SEV-1 production incident occurred during the 2-hour blind spot. Had one occurred, we would have had no visibility.
- **Process improvement**: All monitoring-infrastructure components (Prometheus, AlertManager, Grafana) must have self-monitoring alert coverage before being considered production-ready.
