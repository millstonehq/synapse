---
id: WIKI-024
type: wiki
title: Schema Registry - Usage Patterns
status: approved
owner: Data Team
created: '2024-05-30T15:37:01.496Z'
updated: '2025-06-27T03:19:21.887Z'
tags:
  - wiki
  - data-pipeline
summary: Schema Registry - Usage Patterns
source_repo: https://git.example.com/acme/schema-registry
commit_sha: 9f5d701620343b690e92816d187fea55017f7928
generated_at: '2026-11-22T16:41:17.339Z'
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

This page documents the usage patterns for the Schema Registry Service across data pipeline producers and consumers. All pipeline services that produce or consume Avro-serialized messages must interact with the schema registry. This page covers the three main integration patterns: producer registration, consumer deserialization, and schema evolution.

The registry uses a subject naming convention of `{topic-name}-value` for message value schemas and `{topic-name}-key` for key schemas. Compatibility mode defaults to BACKWARD for all subjects unless explicitly overridden.

## Architecture

The schema registry integration is implemented in two shared libraries used by all pipeline services:

- `pipeline-producer-sdk` (Python) — wraps `confluent-kafka-python` with automatic schema registration and serialization
- `pipeline-consumer-sdk` (Java) — wraps Kafka Streams client with automatic schema lookup and Avro deserialization

Both SDKs cache schemas in-process after the first lookup to avoid repeated REST calls to the registry under high throughput.

## Key Components

### Producer Registration Pattern

Producers register schemas on first use (lazy registration). The SDK performs a `POST /subjects/{subject}/versions` call before the first produce. If the schema already exists and is compatible, the registry returns the existing schema ID. If incompatible, the produce call fails with a `SchemaCompatibilityException`.

```python
from pipeline_producer_sdk import PipelineProducer

producer = PipelineProducer(topic="order.events", schema_path="schemas/order_event.avsc")
producer.produce({"order_id": "abc123", "status": "placed", "amount": 99.99})
```

### Consumer Deserialization Pattern

Consumers embed the schema ID in the first 5 bytes of each Avro message (Confluent wire format: magic byte + 4-byte schema ID + payload). The consumer SDK extracts the schema ID, fetches the schema from the registry (cached), and deserializes the payload.

### Schema Evolution Pattern

New fields must be added with default values to maintain BACKWARD compatibility. Removing fields or changing types requires a compatibility check (`POST /compatibility/subjects/{subject}/versions/latest`) before registering the new version. The pipeline enforces this via a CI pre-check that runs compatibility validation on any `.avsc` file changes.

## Configuration

Schema registry connection configuration (environment variables used by both SDKs):

- `SCHEMA_REGISTRY_URL` — base URL of the registry REST API (e.g., `https://schema-registry.internal:8081`)
- `SCHEMA_REGISTRY_CACHE_TTL_SECONDS` — in-process cache TTL (default: 300)
- `SCHEMA_REGISTRY_MAX_SCHEMAS_PER_SUBJECT` — soft limit to alert when a subject accumulates more than N versions (default: 20)
