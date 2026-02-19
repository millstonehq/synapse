---
id: REPORT-039
type: report
title: Search Infrastructure Capacity Report
status: draft
owner: Search Tech Lead
created: '2024-10-23T04:06:56.114Z'
updated: '2026-02-10T05:12:52.609Z'
tags:
  - report
  - search-platform
summary: Search Infrastructure Capacity Report
company: SearchPlatform
report_month: 2024-04
report_type: company
overall_health: poor
confidence: medium
active_initiatives_count: 5
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| ES data node disk utilization | < 70% | 78% | Below target |
| ES coordinating node CPU (peak) | < 70% | 82% | Below target |
| ES JVM heap pressure | < 75% | 68% | On target |
| Kafka consumer lag (indexing) | < 10K messages | 42K messages | Below target |
| Lambda concurrency (query svc) | < 400 | 312 | On target |
| Redis memory utilization (signals) | < 70% | 61% | On target |

Infrastructure health is poor this period. Elasticsearch disk and CPU are both above target thresholds, and the Kafka consumer lag is elevated due to a backlog caused by embedding API rate limiting earlier in the month. No customer-visible degradation has occurred yet, but the margins are thin.

## Key Highlights

- **Elasticsearch disk growth**: At the current corpus growth rate of 200K documents/month, the cluster will reach the 90% disk threshold in approximately 5 weeks. A storage expansion request (2TB → 3TB per node) has been submitted.
- **Kafka lag investigation**: A 3-hour embedding API rate limit event on April 10 caused the Kafka consumer group to fall 42K messages behind. The backlog was fully cleared within 6 hours. Circuit breaker logic implemented to fall back to no-vector indexing when the embedding API is throttled.
- **Coordinating node scaling**: Two coordinating nodes handle the peak fan-out load during 11am–1pm. CPU regularly exceeds 70% during faceted aggregation queries. Provisioning a third coordinating node.

## Active Initiatives

1. **Elasticsearch storage expansion**: 3TB EBS gp3 volumes requested for each data node. Expected delivery: 2 weeks.
2. **Coordinating node scale-out**: Third coordinating node being provisioned. Load balancer round-robin update required.
3. **Embedding API rate limit resilience**: Circuit breaker to keyword-only indexing mode now deployed to staging.

## Incidents

No incidents this period, but two near-miss events (disk and Kafka lag) require follow-up.

## Risks

- **Critical**: Elasticsearch disk at 78% — 5 weeks until 90% threshold at current growth rate. Storage expansion is the top priority.

## Next Month Focus

- Complete Elasticsearch storage expansion (top priority)
- Deploy coordinating node scale-out
- Promote embedding API circuit breaker to production
- Review Kafka consumer group scaling to reduce lag recovery time
