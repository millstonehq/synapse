---
id: WIKI-012
type: wiki
title: Inventory Event Schema - Reference
status: approved
owner: Inventory Team
created: '2024-02-15T23:05:19.252Z'
updated: '2026-03-20T14:37:51.646Z'
tags:
  - wiki
  - inventory-management
summary: Inventory Event Schema - Reference
source_repo: https://git.example.com/acme/inventory-event-schema
commit_sha: 84958f07b13a6f8fab68701096419f46b995f749
generated_at: '2025-08-15T03:52:13.050Z'
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
importance: medium
example: true
---

## Overview

The `inventory-event-schema` repository is the canonical source of truth for all event schemas flowing through the Inventory Event Bus. It defines Protobuf schemas (with JSON equivalents) for every event type, along with validation rules, versioning policy, and migration guides for breaking changes.

All producers must publish events that conform to a registered schema version. All consumers must declare the schema versions they support. Generated from commit `84958f07b13a6f8fab68701096419f46b995f749`.

## Event Types

The following event types are currently registered in the schema registry:

### `StockReceived`

Published when physical goods arrive at a warehouse location and are counted into on-hand inventory.

```json
{
  "event_type": "StockReceived",
  "schema_version": "2.1",
  "event_id": "uuid-v4",
  "occurred_at": "ISO-8601 timestamp",
  "warehouse_id": "string",
  "location_id": "string",
  "sku_id": "string",
  "quantity": "positive integer",
  "unit_of_measure": "EA | CASE | PALLET",
  "wms_transaction_id": "string (idempotency key)",
  "source": "WMS_WEBHOOK | MANUAL_ADJUSTMENT | CYCLE_COUNT"
}
```

### `StockPicked`

Published when units are removed from a location to fulfill an order.

Key fields: `sku_id`, `location_id`, `quantity` (positive; the delta is applied as negative by the calculator), `order_id`, `fulfillment_id`.

### `StockReserved` / `StockReleased`

Published when inventory is soft-reserved for a pending order or released when an order is cancelled. Affects `reserved_qty` without changing `on_hand_qty`.

### `StockTransferred`

Published when units move between warehouse locations. Generates two events: a `StockPicked` equivalent for the source location and a `StockReceived` equivalent for the destination, linked by a common `transfer_id`.

### `StockAdjusted`

Published for manual corrections and cycle count reconciliation results. Carries a `reason_code` field (CYCLE_COUNT, DAMAGE_WRITE_OFF, RECEIVING_ERROR, SYSTEM_CORRECTION) for audit purposes.

## Key Packages

### `schema/`

Protobuf `.proto` files for each event type. Compiled to language-specific SDKs (Python, TypeScript, Go) published to the internal package registry.

### `validation/`

JSON Schema validators mirroring the Protobuf definitions, used for HTTP webhook payloads where Protobuf is not practical.

### `registry/`

Schema registry client used by producers and consumers to resolve schema versions and validate compatibility.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `protobuf` | 3.25 | Schema definition and compilation |
| `buf` | 1.28 | Protobuf linting and breaking-change detection |
| `jsonschema` | 4.21 | JSON Schema validation (webhook path) |

## Generation Notes

Generated from commit `84958f07b13a6f8fab68701096419f46b995f749`. The generator analyzed Protobuf schema files and extracted message type definitions, field annotations, and registered schema versions.
