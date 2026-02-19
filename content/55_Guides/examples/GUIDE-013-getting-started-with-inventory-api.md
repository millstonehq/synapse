---
id: GUIDE-013
type: guide
title: Getting Started with Inventory API
status: approved
owner: Engineering Team
created: '2024-09-08T12:21:58.100Z'
updated: '2025-06-13T03:39:57.878Z'
tags:
  - guide
  - inventory-management
summary: Getting Started with Inventory API
audience: internal
related_systems:
  - SYSTEM-013
  - SYSTEM-015
related_sops:
  - SOP-028
  - SOP-022
example: true
---

## Prerequisites

Before making your first Inventory API call, make sure you have the following in place.

- **API credentials**: Request an API key from the platform team. Keys are scoped to environments (sandbox, staging, production) — never use a production key during development.
- **Network access**: The Inventory API is only reachable from within the VPN or from approved service accounts. Confirm your local machine or deployment environment has access.
- **Client library or HTTP tool**: You can call the API directly with `curl` or an HTTP client like Postman, or use the internal SDK maintained by the [[SYSTEM-013|Inventory Platform]] team.
- **Familiarity with the data model**: The API operates on SKUs, locations, and adjustment transactions. Reading through the Core Concepts section below before writing code will save you significant debugging time.

## Core Concepts

The Inventory API manages stock levels across one or more warehouse locations. Understanding its three primary resources will help you reason about any operation the API exposes.

A **SKU** (stock-keeping unit) represents a distinct product variant — a specific size, color, or configuration. SKUs are the unit of inventory: you never query "how much product X do I have" in the abstract; you always query against a specific SKU at a specific location.

A **Location** is a physical or logical storage site such as a warehouse, a retail store stockroom, or a virtual fulfillment zone. The [[SYSTEM-015|Warehouse Management System]] owns location records and syncs them into the Inventory API; do not attempt to create or delete locations directly through the Inventory API.

An **Adjustment** is the immutable record of a stock-level change — a receipt, a sale, a write-off, or a manual correction. The API is append-only by design: you never update a quantity directly. Instead, you post an adjustment with a delta (positive or negative), and the API derives the current on-hand quantity from the cumulative adjustment history.

## Getting Started

Follow these steps to make your first successful API call.

1. **Authenticate**: Include your API key in the `Authorization` header as a Bearer token: `Authorization: Bearer <your-api-key>`.
2. **Look up a SKU**: `GET /v1/skus/{sku_id}` returns the SKU record including its description, unit of measure, and any reorder thresholds.
3. **Query on-hand quantity**: `GET /v1/inventory/{sku_id}/locations/{location_id}` returns the current quantity on hand at that location, along with reserved and available quantities.
4. **Post an adjustment**: `POST /v1/inventory/adjustments` with a JSON body specifying `sku_id`, `location_id`, `delta`, and `reason_code`. The API returns the resulting adjustment record with a transaction ID you should log.
5. **Verify the result**: Re-query the on-hand endpoint and confirm the quantity reflects your adjustment. For bulk operations, see [[SOP-028|Bulk Inventory Adjustment SOP]] for guidance on batching and idempotency keys.

All endpoints return JSON. HTTP status codes follow standard semantics: `200` for successful reads, `201` for created adjustments, `400` for validation errors, and `409` for conflicts (e.g., attempting to adjust below zero when negative stock is not permitted for that SKU).

## Common Operations

The following are the operations teams interact with most frequently.

- **Checking available stock before fulfillment**: Query `GET /v1/inventory/{sku_id}/locations/{location_id}` and inspect the `available_quantity` field, which subtracts reserved units from on-hand. Do not use `on_hand_quantity` alone for fulfillment decisions.
- **Reserving inventory for an order**: `POST /v1/inventory/reservations` places a soft hold on units without reducing on-hand. Reservations expire after a configurable TTL (default 30 minutes). See [[SOP-022|Reservation Management SOP]] for the full reservation lifecycle.
- **Releasing a reservation**: `DELETE /v1/inventory/reservations/{reservation_id}` releases the hold. This should be called when an order is cancelled or when a reservation is converted to a fulfilled adjustment.
- **Listing recent adjustments**: `GET /v1/inventory/{sku_id}/adjustments?location_id={id}&limit=50` returns the adjustment history for auditing or reconciliation. Supports cursor-based pagination.
- **Bulk quantity snapshot**: `POST /v1/inventory/snapshots` triggers an asynchronous snapshot of all current quantities. The response includes a job ID you can poll for completion.

## Next Steps

Once you are comfortable with basic reads and adjustments, the following resources will help you go further.

- Review the [[SYSTEM-013|Inventory Platform]] architecture documentation to understand how the API integrates with the broader supply chain systems, including event streaming and downstream consumers.
- Consult [[SOP-028|Bulk Inventory Adjustment SOP]] before building any batch import or reconciliation workflow — it covers idempotency, error handling, and rollback procedures for large-scale operations.
- Consult [[SOP-022|Reservation Management SOP]] if your service participates in the order fulfillment path and needs to manage reservation lifecycles correctly.
- Talk to the platform team before going to production if your integration involves high-frequency adjustments (more than 100 per minute) or cross-location transfers, as these patterns have specific rate limit and ordering considerations.
