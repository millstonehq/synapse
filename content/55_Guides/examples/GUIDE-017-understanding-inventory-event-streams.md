---
id: GUIDE-017
type: guide
title: Understanding Inventory Event Streams
status: approved
owner: Engineering Team
created: '2025-08-19T18:17:01.508Z'
updated: '2026-03-15T03:19:59.424Z'
tags:
  - guide
  - inventory-management
summary: Understanding Inventory Event Streams
audience: customer
related_systems:
  - SYSTEM-012
  - SYSTEM-014
related_sops:
  - SOP-023
  - SOP-024
example: true
---

## What Are Inventory Event Streams?

The inventory platform is built around an event-driven architecture. Rather than exposing a database that other services query directly, the platform publishes a stream of domain events whenever inventory state changes. Any service that needs to react to inventory changes — order management, replenishment, analytics, notifications — subscribes to these event streams and processes events asynchronously.

Understanding how the event stream works is essential for anyone building integrations with the inventory platform or investigating data consistency issues.

## The Core Event Topics

The inventory platform publishes events to four Kafka topics:

- **`inventory.stock-movements`** — every stock quantity change: receipts, adjustments, reservations, releases, write-offs. This is the highest-volume topic.
- **`inventory.sku-lifecycle`** — SKU creation, status changes (active, discontinued, archived), and attribute updates.
- **`inventory.warehouse-events`** — raw events received from warehouse management systems before processing.
- **`inventory.alerts`** — threshold breach events: low stock, stockout, negative quantity. Used by the replenishment and notification services.

## Event Guarantees and Ordering

The inventory event stream provides **at-least-once delivery**. Consumers must implement idempotent processing using the `event_id` field in the event envelope. Processing the same `event_id` twice should produce the same result as processing it once.

Events within a single SKU/warehouse combination are ordered by `occurred_at` timestamp. However, events from different partitions may arrive out of order relative to each other. If your consumer needs a consistent view of a single SKU's stock history, always sort events by `occurred_at` before processing.

Events are retained in Kafka for 7 days. If your consumer falls behind by more than 7 days, it will miss events and will need to rebuild state from the snapshot API.

## Consuming Events

To consume inventory events, your service must join one of the managed consumer groups. Consumer groups are provisioned by the Inventory Platform team; contact #inventory-platform to request one. Do not create ad-hoc consumer groups in production topics without provisioning.

A minimal consumer example in Go:

```go
consumer := kafka.NewConsumer(&kafka.ConfigMap{
    "bootstrap.servers":       "kafka.internal:9092",
    "group.id":                "your-service-name",
    "auto.offset.reset":       "earliest",
    "enable.auto.commit":      "false", // always commit manually
})
consumer.Subscribe([]string{"inventory.stock-movements"}, nil)
```

Always commit offsets manually after successful processing, not before. Committing before processing means that if your service crashes during processing, those events will not be reprocessed.

## Common Mistakes

- **Treating event timestamps as delivery guarantees** — `occurred_at` is when the event happened in the warehouse, not when it was published to Kafka. Events from slow warehouse connections may arrive with `occurred_at` timestamps from minutes or hours ago.
- **Not handling duplicate events** — network retries from the adapter layer mean duplicates are expected. Always deduplicate by `event_id`.
- **Querying the inventory API inside a consumer loop** — this creates a tight coupling between your consumer throughput and the inventory API's request rate limits. Prefer building local state from events rather than making API calls per event.
