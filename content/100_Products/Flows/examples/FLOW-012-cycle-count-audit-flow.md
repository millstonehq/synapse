---
id: FLOW-012
type: flow
title: Cycle Count Audit Flow
status: review
owner: QA Engineer
created: '2025-12-09T05:48:08.664Z'
updated: '2025-02-13T04:54:45.817Z'
tags:
  - flow
  - inventory-management
summary: Cycle Count Audit Flow
feature_area: Inventory Management
related_prds:
  - PRD-014
example: true
---

## Steps

### Step 1: Generate Cycle Count Task

The warehouse manager or operations lead opens the cycle count scheduler in the merchant portal and selects the scope for the count: a specific warehouse location, a product category, or a set of SKUs flagged with high discrepancy risk. The system generates a cycle count task sheet listing each SKU to be counted with its system-recorded `on_hand_qty` hidden from the counter (blind count mode). The count sheet is assigned to a warehouse operative and appears in their task queue.

### Step 2: Perform Physical Count

The warehouse operative navigates to the designated bin locations listed on their task sheet. For each location, they physically count the units present and record the actual quantity in the cycle count interface (via handheld scanner or mobile web). The operative does not see the system quantity until the count is submitted, preventing anchoring bias. If access to a bin is blocked or the location is empty, the operative marks the reason.

### Step 3: Submit Count and Review Variances

The operative submits their completed count. The system compares the submitted physical count against the system `on_hand_qty` for each SKU. Lines with zero variance are auto-approved. Lines with variance beyond the configured tolerance (default: ±2 units or ±2%, whichever is larger) are flagged for supervisor review. The supervisor is notified of flagged lines in their cycle count review queue.

### Step 4: Investigate and Approve Adjustments

The supervisor reviews each flagged line in the cycle count review interface. For each variance:

- The supervisor can approve the adjustment (system quantity will be corrected to match the physical count)
- The supervisor can request a recount (a second operative counts the same location; result replaces the first count)
- The supervisor can reject the adjustment with a note (if the variance is explainable by in-flight transactions, e.g., a receipt not yet processed)

Approved adjustments are queued for processing.

### Step 5: Apply Stock Adjustments and Update Forecasts

For each approved adjustment, the system publishes a `StockAdjusted` event with `source=CYCLE_COUNT` and the delta required to align system quantity with the physical count. The Stock Level Calculator applies the adjustment and the real-time dashboard reflects the corrected stock level within 15 seconds. The Inventory Forecasting Tool (see [[PRD-014|PRD-014]]) recalculates velocity metrics and stockout projections for adjusted SKUs to incorporate the corrected baseline.

## Expected Results

- Physical count results are recorded against each assigned SKU without exposing system quantities to the counter during the count
- Variances within tolerance are auto-approved and adjustments are applied without supervisor intervention
- Variances beyond tolerance are escalated to the supervisor review queue and no stock adjustment is made until the supervisor approves
- `StockAdjusted` events with `source=CYCLE_COUNT` are published for all approved variances; event log preserves the cycle count task reference for auditability
- Forecast projections for adjusted SKUs are recalculated automatically after adjustment events are processed

## User Info

| Field | Value |
|-------|-------|
| Role | Warehouse operative (count) and warehouse supervisor (approval) |
| Permissions | Operative: can submit count results. Supervisor: can approve/reject adjustments and request recounts |
| Test accounts | count-operative@test.example.com, count-supervisor@test.example.com |
| Test warehouse | Warehouse ID: WH-002 (staging environment) |
| Environment | Staging |
