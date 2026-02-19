---
id: TDD-014
type: tdd
title: Warehouse Integration Adapter TDD
status: draft
owner: Tech Lead
created: '2024-02-15T00:22:53.880Z'
updated: '2025-12-01T04:18:58.132Z'
tags:
  - tdd
  - inventory-management
summary: Warehouse Integration Adapter TDD
related_adrs:
  - ADR-0010
  - ADR-0011
example: true
---

## Summary

Design a standardized adapter framework for integrating new warehouse management systems into the inventory platform. As the number of warehouse connections grows, each new integration currently requires bespoke development with inconsistent patterns for authentication, error handling, idempotency, and observability. This framework defines the contract every adapter must implement, provides shared infrastructure (idempotency store, schema validation, DLQ, health reporting), and reduces new warehouse onboarding time from 4-6 weeks to 1-2 weeks. This design builds on the event sourcing model in [[ADR-0010|ADR-0010]] and the DynamoDB idempotency approach in [[ADR-0011|ADR-0011]].

## Overview

- **Standardized adapter contract**: The `WarehouseAdapter` interface defines the lifecycle methods every adapter must implement.
- **Shared infrastructure**: Idempotency checking, schema validation, DLQ routing, health metrics, and retry logic are handled by the framework and not reimplemented per adapter.
- **Configuration-driven authentication**: Per-warehouse credentials and connection parameters are stored in SSM Parameter Store; adapters retrieve them at runtime without hardcoding.
- **Two integration modes**: Webhook (push) and polling (pull), both supported by the framework with mode-specific lifecycle methods.
- **Sandbox testing support**: Framework provides a mock WMS server for local and CI testing of adapters without requiring a live WMS connection.

## Architecture

- **Adapter Registry**: Central registry that maps `warehouse_id` to adapter class and configuration. New adapters are registered in code; the framework routes inbound events to the correct adapter.
- **Webhook Dispatcher**: API Gateway → Lambda handler that receives inbound webhooks, looks up the adapter for the `warehouse_id` path parameter, and invokes `adapter.receive(payload)`.
- **Polling Scheduler**: EventBridge-triggered Lambda that iterates registered polling adapters on their configured schedule and invokes `adapter.poll(cursor)`.
- **Processing Pipeline**: After `receive` or `poll`, the framework handles: signature verification → payload parsing → normalization → idempotency check → schema validation → event bus publish.
- **Health Reporter**: Publishes per-warehouse CloudWatch metrics (events_processed, errors, dlq_depth, sync_lag_seconds) after each processing batch.

## Information Model

- **AdapterConfig**: `warehouse_id`, `warehouse_name`, `integration_mode` (webhook|polling), `polling_interval_seconds`, `auth_type`, `ssm_credential_path`, `adapter_version`
- **RawEvent**: `warehouse_id`, `adapter_id`, `raw_payload`, `received_at`, `source_ip`, `correlation_id`
- **AdapterHealthRecord**: `warehouse_id`, `timestamp`, `events_processed`, `errors`, `dlq_depth`, `sync_lag_p95_seconds`

## Interfaces

- `WarehouseAdapter.receive(rawPayload: Buffer): RawEvent[]` - Parse inbound webhook payload
- `WarehouseAdapter.poll(cursor: string): { events: RawEvent[], nextCursor: string }` - Fetch new events since cursor
- `WarehouseAdapter.normalize(raw: RawEvent): StockEvent` - Map to canonical schema
- `WarehouseAdapter.verifySignature(headers, payload): boolean` - Authenticate inbound payload
- `POST /inbound/{warehouse_id}` - Webhook receiver (framework-managed)
- `GET /health/adapters` - All adapter health summary (framework-managed)

## Files and Layout

```
packages/
  adapter-framework/          - Core framework: pipeline, idempotency, health, DLQ
  mock-wms-server/            - Mock WMS for local/CI testing
adapters/
  {warehouse-id}/
    index.ts                  - Adapter implementation (implements WarehouseAdapter)
    config.ts                 - Adapter configuration schema
    __tests__/                - Unit and integration tests
infra/
  registry.tf                 - Adapter registry DynamoDB table
  ssm.tf                      - SSM parameter path conventions
```

## Work Plan

1. **Phase 1 - Adapter interface and framework core (Week 1-2)**: Define `WarehouseAdapter` interface, shared processing pipeline, SSM credential loading
2. **Phase 2 - Idempotency and DLQ integration (Week 3)**: Integrate DynamoDB idempotency store and DLQ routing from [[ADR-0011|ADR-0011]] design
3. **Phase 3 - Mock WMS server (Week 4)**: Build mock WMS server for webhook and polling modes; add to CI pipeline
4. **Phase 4 - Migrate first adapter (Week 5-6)**: Migrate highest-volume warehouse adapter to framework; validate equivalence with existing adapter
5. **Phase 5 - Health reporting and observability (Week 7)**: CloudWatch metrics, per-warehouse dashboard, alerting rules
6. **Phase 6 - Migrate remaining adapters (Week 8-10)**: Migrate all existing adapters; onboard first new warehouse using framework

## Risks and Mitigations

- **Risk: Framework API changes break existing adapters during migration**: Mitigation: Version the adapter interface; run old and new adapters in parallel during migration with traffic shadowing
- **Risk: Mock WMS server doesn't accurately simulate edge cases (malformed payloads, rate limits)**: Mitigation: Capture anonymized real payloads from existing adapters to seed the mock server's test corpus
- **Risk: SSM Parameter Store latency adds to adapter cold start time**: Mitigation: Cache credentials in Lambda environment after first load; refresh on rotation event via SSM rotation hook
