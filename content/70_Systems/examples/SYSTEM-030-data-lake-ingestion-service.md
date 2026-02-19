---
id: SYSTEM-030
type: system
title: Data Lake Ingestion Service
status: approved
owner: Data Engineering
owner_team: Data Engineering
runtime: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache
created: '2025-01-29T22:27:57.037Z'
updated: '2026-06-29T00:42:53.383Z'
tags:
  - system
  - data-pipeline
summary: Data Lake Ingestion Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/data-lake-ingestion-service
dependencies:
  - Schema Registry Service
  - Data Transformation Engine
runbooks:
  - RUNBOOK-040
  - RUNBOOK-036
example: true
---

## Overview

The Data Lake Ingestion Service is the primary entry point for raw data flowing into the data lake. It consumes events from the Event Streaming Platform, validates message schemas against the Schema Registry Service, and writes validated records to Iceberg tables partitioned by date and source system.

The service ingests approximately 2 million records per day across 40 active source topics. It runs on ECS Fargate (Java 21) with Aurora PostgreSQL for checkpoint tracking and ElastiCache for deduplication. All writes are transactional and include exactly-once semantics via Iceberg's transactional write API.

## Architecture

- **Consumer Layer**: Kafka consumer groups per source topic. Each consumer task reads batches of 500 records, validates schemas, deduplicates against the ElastiCache bloom filter, and stages records in memory before committing the Iceberg write transaction.
- **Schema Validation**: Calls Schema Registry Service synchronously for each new schema version encountered. Schemas are cached in-process for the task lifetime to reduce round-trips.
- **Write Layer**: Iceberg table writer using the Iceberg Java API. Writes are committed atomically per micro-batch (30-second windows). On write failure, the task rolls back and requeues the batch for retry.
- **Checkpoint Layer**: Aurora PostgreSQL records the committed Kafka offsets per topic/partition after each successful Iceberg commit. On restart, the service resumes from the last committed checkpoint.

## Repositories

- [data-lake-ingestion-service](https://git.example.com/acme/data-lake-ingestion-service) - ECS task definitions, consumer code, checkpoint migrations

## Runtime Environment

- **Platform**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache
- **Scaling**: 2-20 Fargate tasks per topic group based on consumer lag; each task uses 4 vCPU and 8Gi memory
- **Deployment**: Blue-green task definition updates; checkpoint state preserved across deployments

## Dependencies

- Schema Registry Service - validates Avro schemas before writing to Iceberg tables
- Data Transformation Engine - reads Iceberg tables produced by this service as the source layer

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Ingestion lag | P95 < 15 minutes from Kafka produce to Iceberg commit |
| Data loss | Zero record loss (at-least-once with deduplication) |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-040|Ingestion Consumer Recovery]]
- [[RUNBOOK-036|Consumer Lag Remediation]]
