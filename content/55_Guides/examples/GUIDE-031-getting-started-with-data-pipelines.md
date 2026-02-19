---
id: GUIDE-031
type: guide
title: Getting Started with Data Pipelines
status: draft
owner: Developer Experience
created: '2024-07-05T19:24:30.616Z'
updated: '2025-01-17T08:53:43.137Z'
tags:
  - guide
  - data-pipeline
summary: Getting Started with Data Pipelines
audience: customer
related_systems:
  - SYSTEM-026
  - SYSTEM-028
related_sops:
  - SOP-053
  - SOP-058
example: true
---

## Why This Matters

Data pipelines are the backbone of every analytics product, ML model, and operational dashboard in the organization. When a pipeline is broken, analysts work from stale numbers, models train on incomplete data, and business decisions are made on incorrect information. Understanding how pipelines work — and how to build them responsibly — is essential for any engineer touching the data platform.

This guide gives you a conceptual foundation for working with data pipelines at this organization. It explains the key systems, the patterns we use, and how to navigate the onboarding path for your first pipeline.

## Key Systems and Concepts

The data platform is built on four core components you will interact with regularly:

- **Airflow** is the pipeline orchestration layer. It schedules and monitors batch DAGs, handles retries, and provides the execution history you need for debugging.
- **Kafka** is the event streaming backbone. It handles real-time data movement between services and feeds both streaming consumers and batch ingestion jobs.
- **The Data Lake** (S3 + Iceberg/Delta Lake) is where all raw and processed data lives. Pipelines read from and write to the lake using partition-aware, idempotent write patterns.
- **The Schema Registry** maintains versioned schemas for all Kafka event types. Every producer must register its schema; consumers validate against it before processing.

Pipelines in this organization are designed to be **idempotent** — running a pipeline twice for the same time window produces the same output as running it once. This makes backfills and failure recovery safe.

## Prerequisites Before Building

Before writing your first pipeline, ensure the following are in place:

- You have read-access to the data lake bucket for your domain
- Your team's service account is provisioned with appropriate IAM permissions
- You have reviewed the naming convention standard so your pipeline IDs, topic names, and dataset names follow the required patterns
- You understand the data classification of the sources you plan to consume — pipelines touching PII data have additional requirements

## Your First Pipeline: Step by Step

1. Start by reading the onboarding checklist linked in the pipeline repository README
2. Design your pipeline with idempotency in mind: use a date-partition write strategy and avoid append-only writes to shared tables
3. Register your output schema in the schema registry before writing any code that produces events
4. Write unit tests for all transformation logic and integration tests that validate output schema and record count expectations
5. Submit your pipeline for review via the standard PR process; attach the completed onboarding checklist
6. After approval, follow the [[SOP-054|Deploy Data Pipeline Changes SOP]] to release to production

## Common Questions

**When should I use Kafka vs. a batch DAG?** Use Kafka for event-driven, near-real-time data flows where latency matters (sub-minute). Use Airflow batch DAGs for scheduled analytical workloads where hourly or daily latency is acceptable and data completeness at a point in time is important.

**How do I handle a backfill?** Follow the [[SOP-053|Backfill Historical Data SOP]]. Never manually delete and re-insert data without following the idempotent write procedure.

## Next Steps

- Review the pipeline naming convention and schema registry standards before starting development
- Familiarize yourself with the [[SOP-051|Restart Failed Airflow DAG SOP]] and [[SOP-058|Clear Stuck Pipeline Task SOP]] — you will need these during on-call
- Attend the data platform onboarding session run by the Data Platform team each sprint
