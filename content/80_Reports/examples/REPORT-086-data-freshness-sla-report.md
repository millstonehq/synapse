---
id: REPORT-086
type: report
title: Data Freshness SLA Report
status: approved
owner: Data Tech Lead
created: '2025-06-23T16:17:29.952Z'
updated: '2026-11-10T23:37:25.771Z'
tags:
  - report
  - data-pipeline
summary: Data Freshness SLA Report
company: DataPipeline
report_month: 2024-03
report_type: company
overall_health: good
confidence: medium
active_initiatives_count: 5
critical_risks_count: 3
example: true
---

## Service Health

Data freshness SLA performance for March 2024. Freshness is measured as end-to-end latency from Kafka event publish to mart-layer Trino query visibility.

| Tier / Table | Freshness SLA | P95 Actual | Status |
|-------------|---------------|-----------|--------|
| Tier-1: orders_daily | < 65 min | 58 min | On target |
| Tier-1: inventory_daily | < 65 min | 61 min | On target |
| Tier-1: session_events_hourly | < 65 min | 72 min | **Breached** |
| Tier-2: customer_profile | < 4 hours | 2h 14m | On target |
| Tier-2: pricing_snapshot | < 4 hours | 3h 41m | On target |
| Tier-3: revenue_attribution | < 24 hours | 18h 22m | On target |

Overall Tier-1 freshness SLA compliance for March: 92.4% of measured windows (target: 99%). The `session_events_hourly` breach drove the miss and is detailed below.

## Key Highlights

- **First monthly freshness SLA report**: This is the inaugural monthly data freshness SLA report, replacing ad-hoc CloudWatch dashboard reviews as the primary mechanism for freshness governance. Baseline compliance metrics establish the benchmark for future improvement.
- **session_events_hourly breach root cause identified**: The `session_events_hourly` table breached the 65-minute SLA on 14 of 31 days in March due to a combination of high-volume session event spikes during peak hours (18:00–20:00 UTC) and undersized ECS ingestion task vCPU. The task was CPU-throttled during the enrichment pipeline processing stage.
- **Tier-1 ingestion task right-sizing initiated**: Engineering team has initiated a capacity change to increase ECS ingestion task vCPU from 2 to 4 for the session events consumer group. Change is scheduled for April 3.
- **Tier-2 and Tier-3 all within SLA**: All non-Tier-1 freshness SLAs met for the full month.

## Active Initiatives

1. **ECS session events task right-sizing** (April 3 target): Increase vCPU for the session events ingestion task to address the CPU throttling causing the Tier-1 SLA breach.
2. **Real-Time Analytics Pipeline (micro-batch)**: The 5-minute flush interval Tier-1 micro-batch pipeline is currently in Week 3 of implementation (PRD-029). Estimated production launch in May 2024; will reduce Tier-1 freshness target to < 15 minutes.
3. **Freshness SLA alerting hardening**: SRE team is implementing per-table freshness alerts in CloudWatch that fire at the 50-minute mark for Tier-1 tables (giving 15-minute warning before SLA breach). Target: complete by April 10.

## Incidents

| Date | Severity | Duration | Impact |
|------|----------|----------|--------|
| Mar 07 | SEV-3 | 42 min | `session_events_hourly` freshness 107 min; ECS task CPU throttled during peak |
| Mar 14 | SEV-3 | 38 min | `session_events_hourly` freshness 103 min; same root cause |
| Mar 21 | SEV-3 | 31 min | `session_events_hourly` freshness 96 min; same root cause |

All three incidents had the same root cause (ECS CPU throttling on session events). No SEV-1 or SEV-2 incidents in March. The Tier-1 breach pattern is a chronic capacity issue, not an acute failure.

## Risks

- **High**: `session_events_hourly` will continue to breach the 65-minute Tier-1 SLA until the April 3 ECS right-sizing change is deployed. Five additional breaches expected in the first 3 days of April before the fix.
- **Medium**: The micro-batch Real-Time Analytics Pipeline (PRD-029) launch in May will introduce a tighter 15-minute Tier-1 SLA for the initial 5 topics. If the micro-batch consumers experience issues, the tighter SLA will result in more frequent breach pages.
- **Low**: The `pricing_snapshot` table is trending toward the 4-hour SLA ceiling (P95 = 3h 41m in March). If growth continues at the current rate, a capacity review will be needed by June.

## Next Month Focus

- Deploy ECS session events task right-sizing on April 3; verify Tier-1 SLA compliance for `session_events_hourly` improves to > 99%
- Complete freshness SLA alerting hardening (50-minute warning alerts for all Tier-1 tables)
- Begin staging validation for the Real-Time Analytics Pipeline micro-batch consumers
