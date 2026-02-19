---
id: FLOW-009
type: flow
title: Stock Intake Processing Flow
status: approved
owner: QA Lead
created: '2025-11-21T23:18:47.233Z'
updated: '2026-07-14T07:41:19.501Z'
tags:
  - flow
  - inventory-management
summary: Stock Intake Processing Flow
feature_area: Inventory Management
related_prds:
  - PRD-012
example: true
---

## Steps

### Step 1: Receive and Log Inbound Shipment

The warehouse operations team receives a physical delivery at the dock. The receiving clerk opens the inbound shipments view in the merchant portal (see [[PRD-012|PRD-012]]) and locates the corresponding purchase order or advance shipping notice. The ASN reference number on the delivery note is scanned or entered manually to associate the physical receipt with the expected shipment record.

### Step 2: Verify Carton Count Against ASN

The clerk counts cartons received and enters the total into the receiving form. The system compares the received carton count against the ASN carton count. If counts match, the flow proceeds. If there is a discrepancy of more than two cartons, the system surfaces a variance warning and requires the clerk to either confirm the count is correct or flag the shipment for supervisor review before continuing.

### Step 3: Scan and Count Units Per SKU

The clerk opens each carton and scans barcodes (GS1-128 or EAN-13) using a handheld scanner connected to the receiving interface. For each scan, the system resolves the barcode to a SKU using the SKU Registry and increments the received unit count for that SKU. Unrecognised barcodes are flagged for manual lookup. The clerk continues until all units in all cartons are scanned or manually counted.

### Step 4: Review Receiving Summary and Confirm

The system displays a line-by-line comparison of expected quantities (from the PO or ASN) versus received quantities for each SKU. Lines where received quantity matches expected quantity are shown in green. Lines with shortages or overages are highlighted. The clerk reviews the summary, adds notes for any discrepancies, and clicks "Confirm Receipt" to submit.

### Step 5: Stock Event Published and Levels Updated

Upon confirmation, the system publishes a `StockReceived` event to the Inventory Event Bus for each SKU with `delta = received_qty`. The Stock Level Calculator consumes the events and increments the `on_hand_qty` for each SKU at the warehouse location. The multi-warehouse aggregated view updates within 15 seconds to reflect the new stock. The PO or ASN status is updated to "received" and the merchant is notified.

## Expected Results

- `StockReceived` events are published for each SKU with accurate deltas reflecting the confirmed received quantity
- Stock levels for all received SKUs update in the multi-warehouse inventory view within 15 seconds of confirmation
- The PO or ASN record is marked as received and the received quantity is recorded against each line item
- Any receiving discrepancies (shortages or overages) are captured in the receipt record with clerk notes
- The warehouse's inbound queue decreases by the processed shipment; no duplicate processing occurs if the confirmation is resubmitted

## User Info

| Field | Value |
|-------|-------|
| Role | Warehouse receiving clerk (authenticated merchant user) |
| Permissions | Can create stock receipts, view open POs and ASNs for their warehouse location |
| Test account | receiving-clerk@test.example.com |
| Test warehouse | Warehouse ID: WH-001 (staging environment) |
| Environment | Staging |
