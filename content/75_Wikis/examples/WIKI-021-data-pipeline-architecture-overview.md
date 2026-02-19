---
id: WIKI-021
type: wiki
title: Data Pipeline - Architecture Overview
status: approved
owner: Data Team
created: '2024-03-18T21:00:37.964Z'
updated: '2026-04-29T08:54:45.123Z'
tags:
  - wiki
  - data-pipeline
summary: Data Pipeline - Architecture Overview
source_repo: https://git.example.com/acme/data-pipeline
commit_sha: 6b6cab6657a34319499b91e41cc3265410b1c316
generated_at: '2026-06-28T03:18:39.486Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: low
example: true
---

## Overview

The data pipeline is a multi-stage architecture that moves data from upstream operational systems through streaming ingestion, schema-validated storage, batch transformation, and quality-checked delivery to analytical consumers. The pipeline is designed for durability and reproducibility: every stage emits checkpoints, failures are retried with backoff, and data can be replayed from any point using Kafka offset commits or Iceberg snapshots.

The pipeline currently processes approximately 2 million events per day from 15 upstream source systems, producing 120 dbt model outputs that serve 8 downstream analytical consumers including the BI platform, ML feature store, and operational dashboards.

## Architecture

The pipeline is organized into four logical layers:

- **Ingestion Layer**: The Event Streaming Platform (Kafka) receives events from upstream producers. The Data Lake Ingestion Service consumes these events, validates schemas against the Schema Registry Service, and writes validated records to raw Iceberg tables partitioned by date and source.
- **Transformation Layer**: The Data Transformation Engine runs dbt models and Python scripts against raw Iceberg tables to produce clean, enriched analytical datasets. The dbt lineage graph determines execution order; the orchestrator schedules tasks as upstream dependencies complete.
- **Quality Layer**: The Data Quality Monitor evaluates rule sets against each dataset after transformation. Violations are classified by severity; CRITICAL violations page on-call and block downstream consumers.
- **Serving Layer**: Clean Iceberg tables are queried directly by Trino for ad-hoc analysis, served to the BI platform via pre-built views, and consumed by the ML feature store via scheduled exports.

## Key Components

- **Event Streaming Platform**: 6-node Kafka cluster; all pipeline events flow through topic-per-source patterns with schema-enforced Avro serialization
- **Schema Registry Service**: Centralizes Avro schema versions and compatibility rules; all producers validate before publish
- **Data Lake Ingestion Service**: Kafka consumer writing Iceberg tables with exactly-once semantics via Aurora checkpoint tracking
- **Data Transformation Engine**: ECS Fargate dbt executor; 120 active models producing tier-1 through tier-3 dataset layers
- **Data Quality Monitor**: Lambda-based rule engine; 400 checks/day evaluating completeness, uniqueness, and statistical integrity

## Configuration

Key configuration parameters that govern pipeline behavior:

- `INGESTION_BATCH_WINDOW_SECONDS`: Micro-batch window for Iceberg writes (default: 30s)
- `DLT_MAX_RETRIES`: Dead-letter topic retry limit before message is quarantined (default: 3)
- `QUALITY_CRITICAL_THRESHOLD`: Violation rate above which a dataset is blocked (default: 0.5%)
- `TRANSFORMATION_TIMEOUT_MINUTES`: Max execution time for a single dbt model before task is failed (default: 60)

## Dependencies

| System | Role |
|--------|------|
| Apache Kafka | Event transport and log storage |
| Apache Iceberg | Table format for all lake storage |
| dbt | Transformation model execution and lineage |
| Trino | Interactive query engine over Iceberg |
| Aurora PostgreSQL | Checkpoint and orchestration state storage |
