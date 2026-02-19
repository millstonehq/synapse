---
id: REPORT-057
type: report
title: Monitoring Platform January 2025 Status Report
status: approved
owner: Monitoring Tech Lead
created: '2025-04-03T12:13:55.166Z'
updated: '2026-04-10T23:26:49.802Z'
tags:
  - report
  - monitoring-stack
summary: Monitoring Platform January 2025 Status Report
company: MonitoringStack
report_month: 2026-04
report_type: company
overall_health: poor
confidence: low
active_initiatives_count: 2
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Prometheus availability | 99.99% | 99.91% | Below target |
| Alert delivery P99 latency | < 30s | 47s | Below target |
| Log ingestion lag P99 | < 10s | 8.2s | On target |
| Trace ingestion lag P99 | < 5s | 4.1s | On target |
| Metrics query P95 | < 2s | 2.8s | Below target |

January was a difficult month for the monitoring platform. A Prometheus TSDB compaction issue on January 30 caused a 2-hour monitoring blackout (see POSTMORTEM-036). Alert delivery latency also spiked during the incident due to AlertManager deduplication delays when the scrape gap introduced phantom resolve/re-fire cycles.

## Key Highlights

- **Monitoring blackout incident (Jan 30)**: Prometheus ran out of disk space during a TSDB compaction cycle, causing a 2-hour gap in metrics ingestion. See POSTMORTEM-036 for full details and action items.
- **Log pipeline stabilization**: After December's disk exhaustion scare, the log pipeline's disk usage monitoring and automated retention enforcement were hardened. No disk-related alerts fired in January.
- **ClickHouse upgrade to 23.8**: The Distributed Tracing Platform's ClickHouse cluster was upgraded from 23.3 to 23.8 LTS. Zero-downtime rolling upgrade completed January 15.

## Active Initiatives

1. **Prometheus disk capacity expansion**: Adding 500GB to each Prometheus pod's local TSDB volume, plus remote write tuning to reduce local retention to 10 days. Estimated completion: Feb 14.
2. **Alert delivery latency investigation**: Profiling AlertManager webhook delivery path to identify the P99 latency regression. Root cause suspected to be alert-management-webhook slow acks.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Jan 30 | SEV-1 | 2 hours | Prometheus disk full — monitoring blackout. All metrics collection paused. See POSTMORTEM-036. |

## Risks

- **Critical**: Prometheus disk pressure is not fully resolved. The capacity expansion is in progress but not complete. If another compaction cycle runs before the expansion is deployed, another blackout is possible.
- **Medium**: Alert delivery P99 latency is 57% above target. Root cause investigation is underway but no fix is deployed yet.

## Next Month Focus

- Deploy Prometheus disk expansion and validate storage headroom
- Resolve alert delivery latency regression
- Conduct POSTMORTEM-036 action item review
- Begin SLO dashboard rollout for all monitoring-stack services
