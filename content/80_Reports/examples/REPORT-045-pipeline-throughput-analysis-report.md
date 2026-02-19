---
id: REPORT-045
type: report
title: Pipeline Throughput Analysis Report
status: approved
owner: Data Tech Lead
created: '2024-01-27T18:44:40.440Z'
updated: '2026-07-10T12:18:25.367Z'
tags:
  - report
  - data-pipeline
summary: Pipeline Throughput Analysis Report
company: DataPipeline
report_month: 2026-04
report_type: company
overall_health: poor
confidence: low
active_initiatives_count: 4
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Peak throughput (events/sec) | 5,000 | 4,320 | Below target |
| Average daily event volume | 2,000,000 | 1,960,000 | Near target |
| Kafka broker disk utilization | < 70% | 58% | On target |
| Consumer group max lag | < 10,000 msgs | 12,400 | Below target |
| Transformation job queue depth | < 50 jobs | 34 | On target |

This report analyzes pipeline throughput metrics over the analysis period. Peak throughput capacity (5,000 events/sec) has not been reached in production, with observed peaks at 4,320 events/sec during morning business hours. Consumer lag on 2 groups is intermittently exceeding the 10,000 message threshold.

## Key Highlights

- **Bottleneck identified in ingestion service**: Profiling shows the Data Lake Ingestion Service ECS tasks are CPU-bound during Iceberg commit operations. Peak write throughput saturates at ~1,800 records/sec per task. Current task count (8) is limiting overall ingestion capacity.
- **Kafka broker disk trending**: At current growth rate (15% month-over-month), broker disk will reach 70% utilization in approximately 6 months. Retention policy review is needed before expansion.
- **Transformation queue depth acceptable**: The orchestration queue peaks at 34 concurrent queued jobs, well within the 50-job threshold. No backpressure observed in the transformation layer.

## Active Initiatives

1. **Ingestion task scaling**: Evaluating increasing max ECS task count from 20 to 40 to handle peak throughput bursts.
2. **Broker disk capacity planning**: Retention policy audit underway; 4 topics identified as candidates for reduced retention (currently 7 days, could be reduced to 3 days without analytics impact).
3. **Consumer lag alerting tuning**: Threshold tightened from 10,000 to 7,500 for tier-1 consumer groups.

## Incidents

No incidents in the analysis period directly related to throughput constraints.

## Risks

- **Medium**: Peak throughput headroom is only 14% above observed peaks (5,000 target vs 4,320 actual peak). A 20% traffic spike from a new upstream producer would breach capacity.
- **Medium**: Two consumer groups intermittently exceeding lag threshold. Root cause traced to a long-running transformation job blocking downstream consumption during peak hours.

## Next Month Focus

- Complete ingestion task scaling evaluation and apply to production
- Finalize broker disk retention policy changes
- Reduce consumer lag alerts to zero sustained breaches for 30 days
