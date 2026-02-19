---
id: MEETING-060
type: meeting
title: Data Lakehouse Design Session
status: accepted
owner: Principal Engineer
created: '2024-12-19T22:54:59.266Z'
updated: '2026-07-24T14:40:46.888Z'
tags:
  - meeting
  - data-pipeline
summary: Data Lakehouse Design Session
company: DataPipeline
topic: Data Lakehouse Design Session
meeting_date: '2024-08-12T01:12:28.038Z'
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

- **Project**: Data Lakehouse Initiative
- **Topic**: Data Lakehouse Design Session
- **Date/Time**: 2024-08-12 10:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Engineering Manager, QA Lead, Product Manager
- **Context**: Kickoff design session to align on lakehouse architecture, table format selection, and ingestion strategy before development begins.

## Observations by Domain

- **Storage Format**: Team aligned on Apache Iceberg as the table format. Key advantages cited: schema evolution, time travel, partition evolution without full rewrites, and broad engine compatibility (Spark, Trino, Flink).
- **Ingestion Layer**: Current batch ingestion via nightly ETL is not meeting latency SLAs for analytics consumers. Discussion centered on adding a streaming ingestion path to reduce data freshness lag from hours to minutes.
- **Query Engine**: Trino is the preferred interactive query engine. Team noted it integrates directly with Iceberg REST catalog and can query both hot (latest partitions) and cold (archived) data uniformly.
- **Catalog**: Decision deferred on catalog implementation - Hive Metastore vs Iceberg REST catalog. REST catalog preferred for decoupled deployments but needs evaluation against existing infrastructure.
- **Data Quality**: No automated quality checks exist at the lakehouse layer today. QA Lead flagged that schema drift from upstream producers has caused silent failures twice this quarter.

## Key Metrics & Data Points

- **Current data freshness lag**: 6-8 hours (batch ETL nightly)
- **Target freshness SLA**: Under 30 minutes for tier-1 datasets
- **Active Iceberg tables in staging**: 12 tables, ~400 GB total
- **Trino query P95 latency (staging)**: 4.2 seconds on unpartitioned scans
- **Upstream producers generating schema changes**: 3 sources in last 90 days

## Preliminary Scorecard Hooks

- Storage Architecture: 3/5 - Iceberg adoption in staging promising, production migration not yet planned
- Ingestion Pipeline: 2/5 - Batch-only path, no streaming capability, freshness SLAs missed
- Query Performance: 3/5 - Trino queries acceptable on small tables, partition pruning not optimized
- Data Quality Gates: 1/5 - No automated checks at lakehouse boundary, schema drift is a known risk
- Catalog Management: 2/5 - Hive Metastore in use, REST catalog migration not scoped

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Schema drift from upstream producers causes silent data corruption | High | High | Tech Lead | Implement schema registry validation at ingestion boundary | 2024-09-15 |
| Iceberg compaction jobs compete with query workloads for cluster resources | Medium | Medium | Principal Engineer | Schedule compaction during low-traffic windows; evaluate dedicated compaction pool | 2024-09-30 |
| Trino partition pruning not effective on legacy table layouts | Medium | Medium | Tech Lead | Refactor partition strategy on top-10 query tables | 2024-10-15 |

## Decisions & Next Steps

### Decisions

- Apache Iceberg confirmed as the table format for all new lakehouse tables
- Streaming ingestion path to be prototyped using existing Event Streaming Platform
- Schema registry validation to be enforced at the ingestion boundary before write

### Action Items

- Draft ADR for Iceberg table format selection (Principal Engineer - 2024-08-26)
- Prototype streaming ingestion using Kafka-to-Iceberg path in staging (Tech Lead - 2024-09-10)
- Evaluate Iceberg REST catalog vs Hive Metastore and produce recommendation doc (Tech Lead - 2024-09-05)

### Follow-ups

- Weekly design sync until streaming ingestion prototype is complete
- Review compaction job performance after first production Iceberg table goes live
