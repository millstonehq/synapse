---
id: GUIDE-016
type: guide
title: Integrating Warehouse Management Systems
status: accepted
owner: Developer Experience
created: '2025-04-30T17:00:40.127Z'
updated: '2025-01-02T02:18:20.881Z'
tags:
  - guide
  - inventory-management
summary: Integrating Warehouse Management Systems
audience: customer
related_systems:
  - SYSTEM-014
  - SYSTEM-011
related_sops:
  - SOP-029
  - SOP-025
example: true
---

## Why This Guide Exists

Integrating a Warehouse Management System (WMS) with the inventory platform is the most complex onboarding task for a new warehouse. The integration must translate WMS-native events into the canonical Warehouse Event Format, handle connectivity interruptions gracefully, and guarantee that no stock movement is lost or double-counted. This guide explains the integration architecture and walks through each stage of building a new WMS adapter.

## Integration Architecture Overview

Every WMS integration uses the same two-layer architecture:

1. **WMS Adapter** — a lightweight service (or set of functions) that connects to the WMS, receives or polls for events, translates them to the canonical event format, and publishes them to the Kafka `inventory.warehouse-events` topic. The adapter runs in the inventory Kubernetes namespace.

2. **Event Processor** — the shared inventory event consumer that reads from Kafka, validates event schemas, and writes stock movements to the inventory database. You do not need to build this; it is already deployed.

The adapter is the only component you need to build for a new WMS integration.

## Building the WMS Adapter

**Step 1: Review the Warehouse Event Format Standard.** Your adapter must produce events that conform to the standard envelope and payload structure. Download the JSON Schema files from the schema registry.

**Step 2: Implement the WMS connection.** Your adapter must handle both push (webhook) and pull (polling) modes, depending on what your WMS supports. Pull adapters should poll on a configurable interval (default: 60 seconds) and use a watermark to avoid reprocessing events.

**Step 3: Implement event translation.** Map each WMS event type to the corresponding canonical `event_type`. Common mappings:

| WMS Event | Canonical Event Type |
|-----------|---------------------|
| RECEIVE | warehouse.receiving.completed |
| SHIP | warehouse.shipment.dispatched |
| ADJUST | warehouse.stock.adjusted |
| TRANSFER | warehouse.stock.transferred |
| COUNT | warehouse.cycle-count.completed |

**Step 4: Publish to Kafka.** Use the shared Kafka producer client from `pkg/kafka`. Set `enable.idempotence=true` to prevent duplicate event publishing during network retries.

**Step 5: Implement error handling.** Failed publishes must be retried with exponential backoff. Events that cannot be published after 5 retries must be written to the local dead letter log for manual review.

## Testing Your Integration

Before deploying to production, use the WMS integration test harness:

```bash
go run ./cmd/wms-test-harness --adapter=[your-adapter] --warehouse-id=[test-warehouse]
```

The test harness sends a sequence of synthetic WMS events through your adapter and validates that the resulting Kafka messages conform to the event schema and that expected stock quantities are produced.

## Going Live

Follow the Onboard New Supplier Feed SOP for the production go-live checklist. Ensure your adapter is configured to connect to production Kafka credentials (stored in the secrets manager, not in config files) and that the warehouse is registered in the inventory platform before the first event is sent.
