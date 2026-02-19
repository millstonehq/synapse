---
id: FLOW-011
type: flow
title: Stock Return Processing Flow
status: approved
owner: QA Engineer
created: '2025-10-31T14:30:52.621Z'
updated: '2025-12-09T00:43:00.979Z'
tags:
  - flow
  - inventory-management
summary: Stock Return Processing Flow
feature_area: Inventory Management
related_prds:
  - PRD-015
example: true
---

## Steps

### Step 1: Receive Return Authorisation

The merchant's customer service team receives a return merchandise authorisation (RMA) request from a customer or supplier. The operations staff opens the returns queue and locates the associated original order or PO. They verify the return is within the accepted return window and that the reason code is valid (damaged, incorrect item, overstock, etc.). A return receipt record is created in draft state with the expected SKU, quantity, and return reason.

### Step 2: Log Physical Receipt of Returned Items

When the returned goods arrive at the warehouse, the receiving team opens the pending returns queue and matches the physical return to the draft return receipt using the RMA reference number. The clerk inspects each returned unit and grades it:

- **Resaleable**: Unit is undamaged and can be returned to available stock
- **Damaged**: Unit requires inspection or write-off before any stock adjustment
- **Wrong item**: Unit received does not match the expected SKU; flagged for investigation

The clerk enters the quantity for each grade and submits the inspection result.

### Step 3: Process Stock Adjustments by Grade

For **resaleable** units, the system publishes a `StockReceived` event with `source=RETURN` and the positive delta is applied to `on_hand_qty` at the warehouse location. These units immediately become available.

For **damaged** units, the system creates a `StockAdjustment` record in pending state. No stock is added until an authorised user reviews and approves the adjustment or writes the units off. If written off, a `StockAdjusted` event with a zero delta is published along with a damage write-off audit record.

For **wrong item** units, the system raises a receiving discrepancy alert and does not adjust stock until the SKU mismatch is resolved by the operations team.

### Step 4: Update Return Record and Notify Supplier or Customer

The return receipt is marked as processed. For supplier returns, the portal notifies the relevant supplier account that the return has been received and the outcome. For customer returns, the customer service team is notified so they can proceed with a refund or replacement order as appropriate. The return record is stored in the transfer and returns audit log for 12 months.

## Expected Results

- Resaleable returned units are reflected in available stock within 15 seconds of the clerk submitting the inspection result
- Damaged units are held in a pending adjustment state until approved by an authorised reviewer; no stock increase occurs without approval
- Wrong-item units generate a discrepancy alert that is visible in the operations dashboard; stock is not adjusted until the mismatch is resolved
- The return record captures the RMA reference, receiving clerk, inspection grades, quantities per grade, and timestamps for full auditability
- No duplicate stock increases occur if the return receipt is re-submitted due to a system error

## User Info

| Field | Value |
|-------|-------|
| Role | Warehouse receiving clerk (authenticated merchant user) |
| Permissions | Can process returns, submit inspection results, view pending returns queue |
| Test account | returns-clerk@test.example.com |
| Test warehouse | Warehouse ID: WH-001 (staging environment) |
| Environment | Staging |
