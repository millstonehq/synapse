---
id: WIKI-011
type: wiki
title: Warehouse Sync - Protocol Documentation
status: approved
owner: Inventory Team
created: '2025-11-02T02:21:42.609Z'
updated: '2026-04-16T17:11:07.521Z'
tags:
  - wiki
  - inventory-management
summary: Warehouse Sync - Protocol Documentation
source_repo: https://git.example.com/acme/warehouse-sync
commit_sha: ab1b54391723444014164eab70cd312d11e34657
generated_at: '2026-05-31T00:43:03.279Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: low
example: true
---

## Overview

The `warehouse-sync` repository implements the protocol layer responsible for receiving, normalizing, and forwarding stock movement data from external warehouse management systems (WMS). Each supported WMS has a dedicated adapter that translates the provider's native protocol into the platform's internal `StockEvent` format.

This page documents the supported protocols, message formats, and adapter extension points. Generated from commit `ab1b54391723444014164eab70cd312d11e34657`.

## Supported Protocols

### Webhook (HTTP Push)

The most common integration mode. The WMS POSTs stock events to a provider-specific endpoint on the Warehouse Sync Gateway. Each endpoint performs:

- HMAC-SHA256 signature verification using the warehouse's pre-shared secret
- Payload decompression (gzip supported)
- Schema validation against the provider's registered event format
- Idempotency check against the `X-WMS-Transaction-ID` header value

Webhook endpoints follow the pattern `/inbound/{warehouse_id}/{event_type}`.

### Polling (HTTP Pull)

Used for WMS providers that do not support outbound webhooks. The gateway polls the provider's REST API on a configurable schedule (1 minute to 24 hours). The adapter tracks a cursor (timestamp or sequence token) to fetch only new events since the last poll.

### EDI (Electronic Data Interchange)

Legacy warehouses transmit stock data via EDI 846 (Inventory Inquiry/Advice) over AS2 transport. The EDI adapter parses X12 transaction sets and maps EDI segments to internal `StockEvent` fields. See the EDI 846 Reference for segment mapping details.

## Key Packages

### `internal/adapter`

Contains one subdirectory per supported WMS provider. Each adapter implements the `WarehouseSyncAdapter` interface:

- `Receive(ctx, rawPayload) ([]RawStockEvent, error)` - parse and validate the raw inbound payload
- `Normalize(raw RawStockEvent) (StockEvent, error)` - map to internal schema
- `AcknowledgeDelivery(ctx, txID string) error` - confirm receipt to the WMS (where required)

### `internal/schema`

Defines the canonical `StockEvent` struct and validation logic. All adapters must produce a valid `StockEvent` before the event is forwarded to the Inventory Event Bus.

### `internal/idempotency`

DynamoDB-backed idempotency store keyed on `(warehouse_id, wms_transaction_id)` with a 7-day TTL. Prevents duplicate processing when a WMS retries a delivery.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| AWS SDK v3 (DynamoDB) | 3.x | Idempotency store |
| `zod` | 3.22 | Runtime schema validation |
| `phin` | 3.7 | Outbound HTTP for polling adapters |
| `node-x12` | 4.2 | EDI X12 parser |

## Generation Notes

Generated from commit `ab1b54391723444014164eab70cd312d11e34657`. The generator analyzed TypeScript/Node.js source files and extracted module structure, interface definitions, and configuration schemas.
