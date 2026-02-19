---
id: TDD-012
type: tdd
title: Inventory Sync Pipeline TDD
status: approved
owner: Senior Engineer
created: '2025-03-14T21:21:10.503Z'
updated: '2026-05-30T16:13:22.841Z'
tags:
  - tdd
  - inventory-management
summary: Inventory Sync Pipeline TDD
related_adrs:
  - ADR-0010
  - ADR-0013
example: true
---

## Summary

Design the inventory synchronization pipeline that ingests stock movement events from multiple warehouse management systems, normalizes them to the internal event schema, deduplicates using idempotency controls, and publishes them to the Inventory Event Bus for downstream processing. This pipeline is the entry point for all externally-sourced stock data and implements the event sourcing model described in [[ADR-0010|ADR-0010]].

The pipeline must handle heterogeneous source protocols (webhooks, polling, EDI), maintain delivery guarantees (at-least-once with deduplication), and provide per-warehouse observability into sync health.

## Overview

- **Protocol diversity**: Each warehouse adapter implements a common interface; protocol details are encapsulated per adapter.
- **Idempotency-first**: Every event carries a warehouse-native transaction ID used as the idempotency key; the pipeline records processed IDs before publishing to prevent duplicates.
- **Schema normalization**: All events are validated and mapped to the canonical `StockEvent` schema before entering the bus.
- **Per-warehouse observability**: Sync lag, error rate, and DLQ depth are tracked per warehouse connection.
- **Dead-letter recovery**: Events that fail after 3 retries are moved to a per-warehouse DLQ with alerting and a replay tool.

## Architecture

- **Inbound Adapters**: One per WMS provider. Each handles authentication, payload parsing, and `RawEvent` extraction. Implemented as Lambda functions (webhook mode) or scheduled ECS tasks (polling mode).
- **Normalization Layer**: Maps `RawEvent` to `StockEvent` using provider-specific field mappings. Validates against the schema registry. Rejects malformed events with structured error logging.
- **Idempotency Store**: DynamoDB table keyed on `(warehouse_id, wms_transaction_id)` with a 7-day TTL. Records processed event IDs before publishing.
- **Event Publisher**: Publishes normalized `StockEvent` to the Inventory Event Bus. Uses retry with backoff for transient failures.
- **DLQ Handler**: Captures permanently-failed events for manual review and replay.

## Information Model

- **RawEvent**: `warehouse_id`, `raw_payload` (provider-native format), `received_at`, `adapter_version`
- **StockEvent**: canonical schema from inventory-event-schema registry (v2.1): `event_type`, `sku_id`, `location_id`, `delta`, `unit_of_measure`, `wms_transaction_id`, `occurred_at`, `source`
- **IdempotencyRecord**: `warehouse_id`, `wms_transaction_id`, `processed_at`, `event_id` (TTL 7 days)

## Interfaces

- `POST /inbound/{warehouse_id}/webhook` - Webhook receiver endpoint per warehouse adapter
- `GET /health/{warehouse_id}` - Per-warehouse sync health (lag, error rate, DLQ depth)
- `POST /admin/replay-dlq/{warehouse_id}` - Trigger DLQ replay for a specific warehouse (admin)
- Internal: `SyncAdapter.receive(rawPayload)`, `SyncAdapter.normalize(rawEvent)` interface per adapter

## Files and Layout

```
adapters/
  warehouse-a/               - Adapter for WMS provider A (webhook, JSON)
  warehouse-b/               - Adapter for WMS provider B (polling, REST)
  warehouse-edi/             - EDI 846 adapter (AS2 transport)
  common/                    - Shared SyncAdapter interface, normalization utilities
lambda/
  webhook-receiver/          - API Gateway-triggered webhook inbound Lambda
  polling-scheduler/         - EventBridge-triggered polling Lambda
infra/
  dynamodb.tf                - Idempotency store table definition
  lambda.tf                  - Function definitions, concurrency limits, DLQ config
```

## Work Plan

1. **Phase 1 - Common adapter interface and schema validation (Week 1-2)**: Define `SyncAdapter` interface, schema registry client, idempotency store client
2. **Phase 2 - First webhook adapter (Week 3-4)**: Implement adapter for highest-volume warehouse; end-to-end test with sandbox WMS
3. **Phase 3 - Polling adapter (Week 5)**: Implement polling adapter with cursor-based incremental fetch; rate limiting and backoff
4. **Phase 4 - EDI adapter (Week 6-7)**: EDI 846 parser, segment terminator validation, UOM cross-reference check
5. **Phase 5 - DLQ and observability (Week 8)**: DLQ handler, per-warehouse health dashboard, replay tool, alerting rules
6. **Phase 6 - Additional adapters and load test (Week 9-10)**: Onboard remaining warehouse adapters; 2x peak throughput test

## Risks and Mitigations

- **Risk: Vendor API documentation delays block adapter development**: Mitigation: Start with highest-priority adapters; use mock WMS sandbox for early development while awaiting vendor docs
- **Risk: EDI parser edge cases in malformed transmissions**: Mitigation: Implement pre-processing validation for segment terminators and UOM cross-reference (lesson from Feb 2025 incident)
- **Risk: DynamoDB write throttling during high-throughput sync bursts**: Mitigation: Use DynamoDB on-demand capacity mode; monitor for throttle events with alert threshold
