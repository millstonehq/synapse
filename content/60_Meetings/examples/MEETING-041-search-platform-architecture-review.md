---
id: MEETING-041
type: meeting
title: Search Platform Architecture Review
status: approved
owner: Product Manager
created: '2024-08-18T14:12:12.345Z'
updated: '2025-04-07T15:17:14.222Z'
tags:
  - meeting
  - search-platform
summary: Search Platform Architecture Review
company: SearchPlatform
topic: Search Platform Architecture Review
meeting_date: '2024-10-20T04:52:16.496Z'
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

- **Project**: Search Platform
- **Topic**: Search Platform Architecture Review
- **Date/Time**: 2024-10-20 10:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, DevOps Lead
- **Attendees (product)**: Product Manager
- **Context**: Quarterly architecture review ahead of planned traffic scaling. Cluster at 65% peak capacity, evaluating index sharding strategy and query routing layer.

## Observations by Domain

- **Indexing Layer**: Current single-index approach is creating hotspot shards during bulk reindex operations; shard routing by content type is recommended
- **Query Routing**: The query service dispatches all request types to a single Elasticsearch endpoint; separate routing for autocomplete vs. full-text queries would improve latency predictability
- **Relevance Pipeline**: BM25 weights are hardcoded in service config rather than externalized; this slows down tuning iteration velocity significantly
- **Monitoring Coverage**: No per-shard latency metrics exist; cluster-level metrics are masking individual node degradation that has caused two incidents this quarter
- **Ingestion Pipeline**: Kafka consumer lag alerting is absent; two silent staleness events went undetected for over 2 hours each
- **Infrastructure**: No auto-scaling policy exists; all scaling has been manual, creating on-call burden during traffic spikes

## Key Metrics & Data Points

- **Cluster peak heap usage**: 82% (high watermark: 85%)
- **P95 query latency**: 340ms (SLO: 500ms; approaching threshold during peak traffic)
- **Indexing throughput**: 12,000 docs/min average, 18,000 docs/min peak
- **Zero-result rate**: 6.2% (target: below 4%)
- **Shard count**: 48 primary shards across 6 data nodes
- **Open tech debt tickets**: 17, of which 5 are rated high priority

## Preliminary Scorecard Hooks

- Indexing Architecture: 3/5 - Functional but single-index design creates operational risk at scale
- Query Performance: 4/5 - P95 within SLO but margin is thin; no headroom for traffic growth without optimization
- Relevance Infrastructure: 2/5 - No externalized config, no offline evaluation pipeline, ranking changes are high-risk
- Observability: 2/5 - Missing per-shard metrics and pipeline lag alerting; two incidents missed this quarter
- Infrastructure Automation: 2/5 - No auto-scaling; manual operations are not sustainable at current growth rate

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Cluster heap exhaustion during peak traffic | High | Medium | DevOps Lead | Add 2 data nodes before next peak traffic event | 2024-11-15 |
| Silent ingestion pipeline stalls | High | High | Search Platform Tech Lead | Add Kafka consumer lag alerting with 10-minute threshold | 2024-10-31 |
| Relevance regressions from hardcoded config changes | Medium | High | Principal Engineer | Externalize ranking config and add offline evaluation gate | 2024-12-01 |
| High zero-result rate degrading user satisfaction | Medium | Certain | Product Manager | Audit top zero-result queries and add synonyms/fallback logic | 2024-11-15 |

## Decisions & Next Steps

### Decisions

- Adopt multi-index sharding strategy with routing by content type for the next major schema revision
- Externalize all ranking configuration into a version-controlled config store before the next ranking change
- Require offline NDCG evaluation as a mandatory gate for all future ranking deployments

### Action Items

- Add Kafka consumer lag alerting for the search ingestion topic (Tech Lead - 2024-10-31)
- Provision 2 additional data nodes to address heap headroom deficit (DevOps Lead - 2024-11-15)
- Design and document the multi-index sharding proposal (Principal Engineer - 2024-11-30)
- Audit top 50 zero-result queries and prioritize synonym additions (Product Manager - 2024-11-15)

### Follow-ups

- Next quarterly architecture review scheduled for January 2025
- Monthly capacity review cadence established starting November 2024
