---
id: REPORT-037
type: report
title: Search Query Performance Report
status: proposed
owner: Search Tech Lead
created: '2025-03-20T14:22:06.377Z'
updated: '2026-08-04T15:05:23.858Z'
tags:
  - report
  - search-platform
summary: Search Query Performance Report
company: SearchPlatform
report_month: 2024-05
report_type: portfolio
overall_health: fair
confidence: high
active_initiatives_count: 1
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| P50 query latency | < 80ms | 71ms | On target |
| P95 query latency | < 200ms | 193ms | On target |
| P99 query latency | < 500ms | 461ms | On target |
| Queries > 1s | < 0.1% | 0.18% | Below target |
| Elasticsearch CPU (peak) | < 70% | 82% | Below target |
| Cache hit rate (query cache) | > 30% | 24% | Below target |

Overall query performance is trending in the right direction. P50 and P95 are within target for the first time in three months. P99 remains within budget. The primary remaining concern is the long-tail of queries exceeding 1 second, which are driven by complex boolean queries and faceted aggregations running on the coordinator nodes.

## Key Highlights

- **Query cache hit rate low**: The `search-content` index query cache is hitting at 24% vs the 30% target. Investigation shows that the high volume of unique filter combinations (especially date-range + category facets) is preventing effective caching. Introducing a coarse date-bucket rounding strategy to improve cache key reuse.
- **Coordinating node CPU pressure**: Peak CPU on coordinating nodes hit 82% during the 11am–1pm traffic window. This is caused by large aggregation fan-outs for faceted search. Evaluated shards-per-coordinator reduction; implementing in the next release.
- **Slow query log analysis**: 94% of queries exceeding 1 second are faceted category aggregations with `size: 1000` buckets. Reducing default aggregation size to 100 and adding circuit-breaker limits for oversized aggregation requests.

## Active Initiatives

1. **Aggregation optimization**: Reduce default bucket size, add request-level circuit breakers for expensive aggregations. Estimated to bring queries-above-1s below 0.1%.

## Incidents

No search-related incidents this period.

## Risks

- **Critical**: Coordinating node CPU at 82% peak — at 90% queries will begin timing out. Node scaling request pending infrastructure approval.
- **Critical**: Query cache hit rate gap means every unique filter combination hits Elasticsearch directly; risk of latency spikes during traffic events.
- **Critical**: Faceted aggregation circuit breaker not yet in place — a single malformed query with a large bucket request could saturate the cluster.

## Next Month Focus

- Deploy aggregation size reduction and circuit breaker
- Implement date-bucket rounding for improved query cache hit rate
- Scale coordinating nodes from 2 to 3 to reduce CPU pressure
