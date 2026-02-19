---
id: FLOW-010
type: flow
title: Inventory Transfer Flow
status: approved
owner: QA Lead
created: '2025-05-30T23:29:57.671Z'
updated: '2026-11-10T23:54:08.418Z'
tags:
  - flow
  - inventory-management
summary: Inventory Transfer Flow
feature_area: Inventory Management
related_prds:
  - PRD-015
example: true
---

## Steps

### Step 1: Identify Transfer Candidates

The merchant operations staff opens the multi-warehouse inventory view and sorts by stock imbalance indicator. SKUs flagged as having more than 80% of available stock concentrated in a single warehouse are candidates for inter-warehouse transfer. The user selects a SKU and reviews its per-warehouse stock breakdown to identify the source warehouse (overstocked) and destination warehouse (understocked).

### Step 2: Create a Transfer Request

The user clicks "Create Transfer" on the selected SKU. The transfer request form opens pre-populated with the source and destination warehouse, and the suggested transfer quantity (defaulting to the quantity that would bring both locations to rough parity). The user reviews and adjusts the transfer quantity, adds an optional reference note, and submits the transfer request.

### Step 3: Reserve Stock at Source Warehouse

The system creates a `TransferReservation` at the source warehouse, reducing the available quantity for the transfer quantity without yet incrementing stock at the destination. The multi-warehouse view shows the reserved quantity as "in-transfer" at the source location and displays the transfer request as "pending dispatch" in the transfer queue.

### Step 4: Confirm Dispatch from Source

The source warehouse operations team opens their outbound queue and locates the transfer request. They pick and pack the items, scan each unit to confirm the actual dispatch quantity, and submit the dispatch confirmation. If the dispatched quantity differs from the requested quantity (e.g., fewer units are available on the shelf), the system records the actual dispatched quantity and updates the transfer record accordingly.

### Step 5: Confirm Receipt at Destination

When the goods arrive at the destination warehouse, the receiving team opens the inbound transfer queue and processes the receipt in the same way as a supplier delivery (see FLOW-009 for receiving step details). The clerk scans units against the transfer manifest. Upon confirmation, the system publishes a `StockTransferred` event: `delta = -dispatched_qty` at the source and `delta = +received_qty` at the destination. Stock levels update in both warehouse views within 15 seconds.

## Expected Results

- A `StockTransferred` event is published for each SKU: negative delta at source warehouse and positive delta at destination warehouse
- Available stock at source decreases by the dispatched quantity immediately upon dispatch confirmation
- Available stock at destination increases by the received quantity immediately upon receipt confirmation
- The inter-warehouse imbalance indicator for the transferred SKU recalculates; the flag clears if concentration drops below the 80% threshold
- The transfer record retains dispatch and receipt quantities for audit; any variance between dispatched and received is flagged in the transfer history

## User Info

| Field | Value |
|-------|-------|
| Role | Merchant operations staff (authenticated merchant user with multi-warehouse access) |
| Permissions | Can create transfer requests, confirm dispatch, confirm receipt at their warehouse location |
| Test account | ops-staff@test.example.com |
| Test warehouses | Source: WH-001, Destination: WH-003 (staging environment) |
| Environment | Staging |
