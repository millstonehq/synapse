---
id: GUIDE-018
type: guide
title: Testing Inventory Sync Pipelines
status: approved
owner: Developer Experience
created: '2024-10-10T18:50:38.994Z'
updated: '2025-02-21T06:23:59.927Z'
tags:
  - guide
  - inventory-management
summary: Testing Inventory Sync Pipelines
audience: partner
related_systems:
  - SYSTEM-012
  - SYSTEM-014
related_sops:
  - SOP-026
  - SOP-024
example: true
---

## Why Testing Sync Pipelines Is Hard

Inventory sync pipelines involve multiple distributed components: the WMS adapter, the Kafka event bus, the event processor, and the inventory database. Each boundary is a potential failure point. Testing these pipelines effectively requires simulating realistic failure modes — not just the happy path — because the consequences of a bug in production are stock discrepancies that can take days to reconcile.

This guide covers the testing strategy for inventory sync pipelines at each level: unit, integration, and end-to-end.

## Unit Testing Event Translation

The most testable part of a sync pipeline is the event translation logic in the WMS adapter. Write unit tests for each WMS event type to verify the translation produces a valid canonical event:

```go
func TestTranslateReceiveEvent(t *testing.T) {
    wmsEvent := WMSEvent{Type: "RECEIVE", SKUID: "ELEC-ACME-HDPH200-BLK", Qty: 100}
    canonical, err := TranslateEvent(wmsEvent)
    assert.NoError(t, err)
    assert.Equal(t, "warehouse.receiving.completed", canonical.EventType)
    assert.Equal(t, 100, canonical.Payload.QuantityDelta)
    assert.NotEmpty(t, canonical.EventID) // must be a valid UUID
}
```

Run these tests with no external dependencies. Cover all mapped event types and edge cases: zero quantity events, negative adjustments, events with missing optional fields.

## Integration Testing with the Local Stack

Use the Docker Compose development environment (described in the Local Development Guide) to run integration tests that exercise the full sync pipeline:

```bash
go test ./tests/integration/... -tags=integration -v
```

The integration test suite sends synthetic WMS events through the adapter, waits for them to be processed by the event processor, and queries the inventory API to verify the expected stock changes occurred. Tests include:

- Happy path: single stock movement event end-to-end
- Duplicate event handling: same `event_id` sent twice should result in one stock movement
- Out-of-order events: events with older `occurred_at` than the current state should not produce negative quantities
- Large batch: 10,000 events sent in rapid succession to verify ordering is preserved

## Testing Failure Scenarios

The most important test cases are failure modes. The test harness includes a fault injection mode:

```bash
go run ./cmd/wms-test-harness --fault-mode=kafka-timeout --adapter=[your-adapter]
```

Available fault modes:
- `kafka-timeout` — simulates Kafka publish timeouts; verify events are retried and eventually delivered
- `duplicate-events` — sends each event twice; verify idempotency in the processor
- `schema-invalid` — sends malformed events; verify they land in the DLQ and do not corrupt inventory state
- `warehouse-api-slow` — simulates slow WMS responses; verify the adapter does not time out or lose events

Run all fault modes as part of your integration sign-off before production deployment.

## End-to-End Validation in Staging

Before promoting a new adapter or pipeline change to production, run the staging validation suite:

```bash
go run ./cmd/staging-validator --warehouse-id=[staging-warehouse] --duration=30m
```

The validator generates a known sequence of stock movements in the staging WMS, waits for them to propagate through the full pipeline, and compares the final inventory state in staging against the expected quantities. A passing validation with zero discrepancies is required for production sign-off.
