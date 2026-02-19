---
id: PRD-029
type: prd
title: Real-Time Analytics Pipeline PRD
status: review
owner: Product Manager
created: '2025-10-12T14:00:54.655Z'
updated: '2026-11-02T03:44:24.885Z'
tags:
  - prd
  - data-pipeline
summary: Real-Time Analytics Pipeline PRD
related_tdds:
  - TDD-026
  - TDD-030
example: true
related_standards:
  - STANDARD-031
---

## Summary

Build a Real-Time Analytics Pipeline that reduces end-to-end data freshness for Tier-1 analytics dashboards from the current 1–4 hour batch window to under 15 minutes. The pipeline uses the existing Kafka Event Streaming Platform and Apache Iceberg data lake but introduces a micro-batch ingestion path with 5-minute flush intervals, replacing the current hourly batch ECS ingestion tasks for high-priority topics. Technical design is driven by [[TDD-026|TDD-026: Real-Time Event Processing Engine]] and [[TDD-030|TDD-030: Data Lineage Tracker]], and must comply with [[STANDARD-031|STANDARD-031]].

## Goals

- Reduce Tier-1 dashboard data freshness from 1–4 hours to < 15 minutes end-to-end
- Enable product teams to build near-real-time operational dashboards on Iceberg data without custom pipeline requests
- Maintain at-least-once delivery guarantees with full recovery via Kafka retention
- Launch without increasing infrastructure costs by more than 15%

## In Scope

- Micro-batch ingestion path for 5 designated Tier-1 Kafka topics (orders, inventory, user-events, pricing-updates, session-events)
- 5-minute Iceberg flush interval for micro-batch consumers (down from 60 minutes)
- dbt incremental model updates on 15-minute schedule for Tier-1 mart tables
- Data freshness SLA alert: page if any Tier-1 table is > 15 minutes stale
- Grafana dashboard for real-time pipeline latency monitoring

## Out of Scope

- True streaming (sub-second) pipeline (requires Flink or Spark Streaming; out of scope for this iteration)
- All non-Tier-1 topics (remain on hourly batch schedule)
- Schema changes to existing Tier-1 topics (separate schema evolution process)
- Multi-region replication

## Users and Flows

**Product Analysts**: Build operational dashboards that require data fresher than 1 hour (e.g., intraday order volume, live inventory levels, active session counts); the 15-minute freshness window unlocks dashboards previously requiring direct database access.

**Data Engineering On-Call**: Monitor micro-batch pipeline health via updated Grafana dashboard; receive pages if freshness SLA is breached.

**Platform Engineering**: Validate that the 5-minute flush interval does not create excessive Iceberg small files; confirm compaction schedule is adequate.

## Requirements

- Micro-batch consumers for Tier-1 topics flush to Iceberg every 5 minutes
- dbt incremental models for Tier-1 mart tables execute every 15 minutes on an Airflow schedule
- End-to-end freshness (Kafka event → dashboard-queryable mart row) must be < 15 minutes at P95
- All micro-batch consumers must maintain the existing at-least-once checkpoint guarantee (offset committed after Iceberg commit)
- Iceberg compaction for Tier-1 tables runs every 4 hours to prevent small file accumulation
- Consumer lag alert fires if any Tier-1 topic lag exceeds 10,000 messages

## KPIs

- **End-to-end freshness**: P95 < 15 minutes from Kafka event publish to mart row visible in Trino
- **SLA compliance**: Tier-1 freshness SLA (< 15 minutes) met for > 99% of 15-minute windows per month
- **Cost increase**: Infrastructure cost increase < 15% vs. hourly batch baseline
- **Adoption**: At least 3 product teams launch operational dashboards using the real-time pipeline within 60 days

## Information Architecture

- Tier-1 topic configuration maintained in the data-pipeline repository as a YAML list
- Micro-batch consumer task definitions are variants of the existing ECS ingestion task with modified flush interval configuration
- Tier-1 dbt models tagged `tier1_realtime` for selective scheduling

## Data Model

Core entities:

- **MicroBatchConfig**: Configuration per Tier-1 topic. Fields: `topic`, `consumer_group`, `flush_interval_seconds`, `max_buffer_records`, `sla_freshness_minutes`
- **FreshnessStatus**: Operational metric. Fields: `topic`, `mart_table`, `last_flush_at`, `last_dbt_run_at`, `current_lag`, `sla_breach`

## Non-Functional

- Micro-batch consumers must not increase end-to-end latency beyond P95 = 15 minutes under peak Kafka throughput (5 MB/s per topic)
- All existing at-least-once delivery guarantees must be preserved; no data loss is acceptable
- Iceberg small file target: data files > 64 MB after compaction; max 200 files per partition before compaction triggers

## Constraints

- Must use the existing ECS Fargate ingestion infrastructure; no new streaming compute cluster
- Must use the existing Airflow MWAA environment for dbt scheduling; 15-minute DAG interval must fit within MWAA worker capacity
- Tier-1 topic list is limited to 5 topics in v1 to manage operational risk

## Risks

- **Small file explosion**: 5-minute flushes create 12× more Iceberg files per hour vs. hourly batch. Mitigation: 4-hour compaction schedule for Tier-1 tables; alert if partition file count exceeds 200.
- **dbt 15-minute scheduling**: Running dbt every 15 minutes increases MWAA worker utilization. Mitigation: Tier-1 dbt runs use `--select tag:tier1_realtime` to limit model scope; estimated runtime < 8 minutes.
- **Freshness SLA breach causes alert fatigue**: 15-minute SLA is tighter than existing SLAs. Mitigation: 5-minute grace window before page; warning-level alert at 12 minutes.

## Milestones

### M1: Micro-Batch Consumers (Week 1-3)

#### Deliverables

- ECS task configurations for 5 Tier-1 topics with 5-minute flush interval
- Checkpoint guarantee preserved and covered by integration tests
- Consumer lag and freshness CloudWatch metrics

#### Acceptance Criteria

- Tier-1 topics flushing to Iceberg every 5 minutes (verified by CloudWatch flush metric)
- No data loss on ECS task restart (checkpoint integration test passes)
- Consumer lag alert fires correctly in test environment

### M2: dbt 15-Minute Scheduling (Week 4-5)

#### Deliverables

- Airflow DAG for 15-minute dbt incremental runs on Tier-1 mart models
- Freshness SLA alert wired to PagerDuty
- Grafana dashboard for real-time pipeline latency

#### Acceptance Criteria

- End-to-end freshness P95 < 15 minutes in staging environment
- Freshness SLA alert pages within 5 minutes of a simulated 15-minute breach
- dbt 15-minute runs complete in < 8 minutes (P95)

### M3: Compaction and Production Launch (Week 6-7)

#### Deliverables

- 4-hour compaction schedule for Tier-1 Iceberg tables
- Production deployment of micro-batch consumers and 15-minute dbt schedule
- Small file monitoring alert

#### Acceptance Criteria

- Production end-to-end freshness P95 < 15 minutes over first 7-day window
- Iceberg file count per partition stable (not growing unbounded) after 7 days
- Infrastructure cost increase < 15% vs. pre-launch baseline
