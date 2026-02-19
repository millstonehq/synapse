---
id: REPORT-047
type: report
title: Kafka Cluster Capacity Report
status: review
owner: Data Tech Lead
created: '2024-10-07T22:51:26.203Z'
updated: '2025-08-09T12:36:34.838Z'
tags:
  - report
  - data-pipeline
summary: Kafka Cluster Capacity Report
company: DataPipeline
report_month: 2026-11
report_type: analytics
overall_health: excellent
confidence: low
active_initiatives_count: 6
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Broker disk utilization | < 70% | 58% | On target |
| Broker CPU utilization | < 60% | 41% | On target |
| Network bytes in/out | < 800 MiB/s | 340 MiB/s | On target |
| Under-replicated partitions | 0 | 0 | On target |
| Active topics | < 200 | 147 | On target |
| Consumer groups | Tracked | 38 active | Informational |

Current Kafka cluster capacity is healthy with comfortable headroom across all dimensions. At the current growth rate of 15% month-over-month in event volume, disk utilization will reach the 70% threshold in approximately 5 months. Proactive expansion planning is recommended.

## Key Highlights

- **Disk growth trend**: Monthly disk growth is averaging 8% per broker. At this rate, disk reaches 70% threshold in November 2025. Retention policy changes for 4 low-priority topics could extend this by 2 months without requiring hardware expansion.
- **Topic proliferation**: Topic count has grown from 98 to 147 in 6 months (+50%). 23 topics have zero active consumer groups and are candidates for cleanup after data retention period expires.
- **Partition balance**: All 147 topics are evenly distributed across brokers with rack-aware assignment. No under-replicated partitions in the past 30 days.

## Active Initiatives

1. **Retention policy review**: Analyzing 4 topics with 7-day retention that could safely be reduced to 3 days; combined savings of 2.8 TB across cluster.
2. **Topic cleanup**: Identifying and deprecating 23 inactive topics after confirming no consumers have outstanding offsets.
3. **Capacity expansion planning**: Evaluating broker count increase from 6 to 9 for Q4; scoping hardware and license costs.

## Incidents

No capacity-related incidents in the reporting period.

## Risks

- **Critical**: At current growth rate, disk capacity threshold reached by November 2025 without intervention. Broker expansion or retention reduction required.
- **Medium**: Topic count growing without formal lifecycle management process; inactive topics accumulate and consume retention storage.

## Next Month Focus

- Finalize retention policy changes for 4 targeted topics and deploy
- Complete inactive topic cleanup for 23 candidates
- Submit capacity expansion proposal for Q4 broker expansion
