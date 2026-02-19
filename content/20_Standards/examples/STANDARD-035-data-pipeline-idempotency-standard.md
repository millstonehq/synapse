---
id: STANDARD-035
type: standard
title: Data Pipeline Idempotency Standard
status: proposed
owner: Compliance Officer
created: '2024-08-29T20:17:42.323Z'
updated: '2025-05-05T08:06:31.784Z'
tags:
  - standard
  - data-pipeline
summary: Data Pipeline Idempotency Standard
related_policies:
  - POLICY-029
  - POLICY-026
example: true
related_systems:
  - SYSTEM-029
  - SYSTEM-026
---

## Area

This standard defines idempotency requirements for all data pipelines to ensure that re-running a pipeline for a given time partition or event window produces the same output as the first run. It applies to batch pipelines, Kafka consumer processors, and any pipeline stage that writes to persistent storage.

## Controls

- All pipeline writes to the data lake or warehouse must use an upsert or overwrite strategy keyed on a deterministic partition key; append-only writes without deduplication are prohibited in production
- Pipeline tasks must be designed such that re-execution of a failed task produces identical output; side-effecting operations must be guarded with idempotency keys
- Kafka consumer processors must implement at-least-once processing with deduplication logic using message offset or a unique event ID
- Backfill operations must use the same idempotent write path as regular runs; separate backfill code paths are prohibited
- Idempotency must be validated via automated tests that run the pipeline twice against the same input and assert output equality

## Compliance Mappings

- SOC 2: CC6.1 (Logical access and data integrity controls)
- ISO 27001: A.12.1.1 (Documented operating procedures)

## Related Policies

- [[POLICY-029|PII Masking in Pipelines Policy]]
- [[POLICY-026|Data Pipeline Access Control Policy]]
