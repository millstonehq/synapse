---
id: ADR-0032
type: adr
title: Choose Grafana Loki for Log Aggregation
status: review
owner: Staff Engineer
created: '2024-03-10T07:43:49.663Z'
updated: '2026-07-28T19:33:16.167Z'
tags:
  - adr
  - monitoring-stack
summary: Choose Grafana Loki for Log Aggregation
example: true
---

## Context

The Log Aggregation Pipeline currently uses SQL Server as its indexing backend, which was a pragmatic choice given existing team expertise but is showing limitations at scale. Full-text indexing in SQL Server is expensive, the columnar query performance on high-volume log data is poor for time-range scans, and the licensing cost is significant. As log volume grows with service onboarding, we need to evaluate whether to continue investing in the SQL Server backend or migrate to a purpose-built log aggregation system.

This ADR specifically evaluates Grafana Loki as an alternative backend. Loki's design philosophy — index only labels, not full log text, and compress log streams by label set — trades full-text search for dramatically reduced storage costs and operational simplicity. Log data is stored in object storage (Azure Blob / S3) with a small local index, making it horizontally scalable without managing a database cluster.

The evaluation must weigh the migration cost (re-plumbing Fluent Bit forwarders and rebuilding log queries in LogQL) against the long-term operational and cost benefits.

## Decision

**Deferred.** This ADR is in review and a final decision has not been made. The evaluation is ongoing.

Current status: A Loki proof-of-concept was deployed in the staging environment. Key findings from the POC:
- Storage cost: 78% reduction compared to SQL Server for equivalent 30-day log retention
- Full-text search: Loki's grep-based search is slower than SQL Server's full-text index for unstructured log content, but acceptable for structured JSON logs (label filter + line filter)
- Query language (LogQL): Engineers found LogQL intuitive; the learning curve was approximately 1 day for engineers already familiar with PromQL

A final decision is expected after the POC team completes load testing at 2x production volume.

## Consequences

**Positive (if Loki is adopted):**
- 78% estimated reduction in log storage costs
- Object storage backend scales horizontally without database cluster management
- Native Grafana integration: unified dashboards with Prometheus metrics and Loki logs side-by-side
- No licensing cost (open source)

**Negative (if Loki is adopted):**
- Full-text search on unstructured log messages is slower than SQL Server full-text index
- Migration effort: re-configure Fluent Bit, rebuild log-based alert rules in LogQL, train engineers on LogQL
- Loki's compactor and ruler components add operational complexity compared to a single SQL Server instance

**Neutral:**
- Loki and SQL Server can run in parallel during a migration window, allowing gradual query migration

## Alternatives Considered

**Keep SQL Server (status quo):**
- Pro: No migration cost; team expertise; strong full-text indexing
- Con: High storage cost; poor time-range scan performance; licensing expense; no horizontal scaling
- May be retained: If Loki's search performance proves insufficient for the team's log investigation workflows, SQL Server may be retained for the hot storage tier.

**OpenSearch / Elasticsearch:**
- Pro: Best-in-class full-text search, mature ecosystem, strong Kibana visualization
- Con: High operational overhead (JVM tuning, shard management); higher storage cost than Loki; license concerns (Elastic License v2 for recent versions)
- Rejected from further consideration because: Operational complexity and cost do not improve on the current SQL Server situation sufficiently to justify migration cost.
