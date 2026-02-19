---
id: PRD-013
type: prd
title: Automated Reorder System PRD
status: approved
owner: Senior PM
created: '2024-09-01T13:17:07.502Z'
updated: '2026-03-05T13:53:57.553Z'
tags:
  - prd
  - inventory-management
summary: Automated Reorder System PRD
related_tdds:
  - TDD-015
  - TDD-012
example: true
related_standards:
  - STANDARD-016
---

## Summary

Build an automated reorder system that monitors stock levels against configurable reorder points and automatically generates purchase orders to suppliers when thresholds are breached. This eliminates the manual daily stock review process currently performed by merchant operations teams and reduces stockout events caused by delayed reorder decisions.

The system integrates with the stock reservation model in [[TDD-015|TDD-015]] to ensure reorder triggers account for reserved stock in the availability calculation.

## Goals

- Eliminate manual daily stock reviews for merchants who opt into automated reordering
- Reduce stockout incidents by 40% within 6 months of launch
- Allow merchants to define reorder rules at the SKU level with configurable thresholds and order quantities
- Generate purchase orders automatically and track them through to receipt confirmation

## In Scope

- Configurable reorder point (ROP) and reorder quantity per SKU per warehouse
- Automatic purchase order (PO) generation when available stock falls below the ROP
- PO routing to suppliers via email or supplier portal API
- PO tracking: created, sent, confirmed, in-transit, received states
- Reorder history log per SKU
- Manual override: merchants can pause automatic reordering per SKU or globally
- Lead time tracking per supplier to inform ROP calculations
- Notification: email/webhook to merchant when a reorder is triggered

## Out of Scope

- Demand forecasting-based dynamic ROP calculation (separate PRD)
- Multi-supplier selection and cost comparison
- EDI PO transmission (v2)
- Receiving workflow and goods receipt processing (separate initiative)
- Automated supplier payment

## Users and Flows

**Merchants with recurring stock** are the primary users. They configure a reorder point and standard order quantity for each SKU. When the system detects that available stock has crossed the threshold, a PO is generated and sent to the configured supplier without manual intervention. Merchants receive a notification and can review the pending PO before it is sent (optional approval step).

**Merchant operations staff** monitor the reorder queue dashboard to see which POs have been generated, confirm supplier acknowledgements, and update tracking information for in-transit shipments. They can pause automatic reordering during promotions or supplier transitions.

**Suppliers** receive POs via email or API. The supplier portal self-service feature (see Supplier Portal PRD) allows suppliers to acknowledge POs and provide estimated delivery dates directly, reducing email back-and-forth.

## Requirements

- Evaluate reorder eligibility for all active SKUs every 15 minutes
- Generate a PO automatically when available stock ≤ configured reorder point
- Support configurable reorder quantity, minimum order quantity, and order quantity rounding to supplier pack sizes
- Route PO to supplier via email (always) and supplier API (if integrated)
- Track PO state through lifecycle: draft → sent → acknowledged → in-transit → received
- Allow merchants to enable/disable automatic reordering globally and per-SKU
- Prevent duplicate POs: do not generate a new PO for a SKU that already has an open in-transit PO
- Send email and configurable webhook notification to merchant when reorder is triggered
- Store reorder history with trigger reason (which threshold was crossed, what the stock level was at trigger time)

## KPIs

- **Stockout reduction**: Stockout events for auto-reorder-enabled SKUs reduced by 40% within 6 months
- **PO generation accuracy**: < 1% of generated POs require manual cancellation due to incorrect trigger
- **Reorder evaluation latency**: All active SKUs evaluated within 15 minutes of a stock level change
- **Merchant adoption**: 40% of eligible merchants activate automatic reordering within 90 days of launch

## Information Architecture

- Reorder configuration in merchant portal: `portal.example.com/inventory/reorder-settings`
- PO queue and tracking: `portal.example.com/inventory/purchase-orders`
- Reorder evaluation service calls the Stock Level Calculator's availability endpoint (using CQRS read model)
- PO generation uses the inventory sync pipeline architecture from [[TDD-012|TDD-012]] for receiving PO status updates
- Reorder rules and POs stored in a dedicated PostgreSQL schema

## Data Model

- **ReorderRule**: `rule_id`, `merchant_id`, `sku_id`, `location_id`, `reorder_point_qty`, `reorder_qty`, `supplier_id`, `pack_size`, `lead_time_days`, `enabled` (bool)
- **PurchaseOrder**: `po_id`, `merchant_id`, `supplier_id`, `sku_id`, `location_id`, `ordered_qty`, `status`, `triggered_by_stock_qty`, `created_at`, `sent_at`, `acknowledged_at`, `expected_delivery_date`, `received_at`
- **ReorderHistory**: `history_id`, `sku_id`, `location_id`, `trigger_stock_qty`, `reorder_point_qty`, `po_id`, `triggered_at`

## Non-Functional

- Reorder evaluation must handle 500,000 active reorder rules within the 15-minute evaluation window
- PO generation is idempotent: re-evaluating a SKU that already has a triggered PO does not create a duplicate
- PO emails must be delivered within 5 minutes of trigger
- All PO state changes logged for audit (who changed what, when)

## Constraints

- Reorder evaluation reads from the CQRS Redis read model; must not query PostgreSQL directly at evaluation scale
- PO generation requires a confirmed supplier configuration; SKUs without a supplier configured are excluded from automatic reordering
- Email delivery uses the existing platform email service

## Risks

- **Duplicate PO generation** if the open-PO check races with concurrent evaluation runs. Mitigation: Use a distributed lock (Redis SETNX) per (sku_id, location_id) during PO generation.
- **False triggers during event replay or reconciliation adjustments** could generate erroneous POs. Mitigation: Mark reconciliation events with a `source=RECONCILIATION` flag and exclude them from reorder threshold evaluation.
- **Merchant misconfiguration** (e.g., reorder point set too high) could generate excessive POs. Mitigation: Add a rate limit of 3 POs per SKU per 24 hours and alert if the limit is reached.

## Milestones

### M1: Reorder Rules and Evaluation Engine (Week 1-4)

#### Deliverables

- Reorder rule configuration UI (reorder point, quantity, supplier, pack size)
- Reorder evaluation engine running on 15-minute schedule
- PO generation (draft state) when threshold crossed

#### Acceptance Criteria

- Reorder rule can be configured for a SKU and triggers correctly when stock drops below threshold in test environment
- No duplicate POs generated for a SKU with an open in-transit PO
- Evaluation completes within 15 minutes for 500,000 simulated rules in load test

### M2: PO Routing and Tracking (Week 5-7)

#### Deliverables

- PO email routing to configured supplier
- PO state tracking (draft → sent → acknowledged → in-transit → received)
- Merchant PO queue dashboard and notifications

#### Acceptance Criteria

- PO email delivered to supplier within 5 minutes of trigger
- Merchant receives notification email and sees PO in dashboard within 10 minutes
- PO state transitions correctly logged in audit trail

### M3: Production Rollout (Week 8-10)

#### Deliverables

- Beta rollout to 20 pilot merchants with manual PO approval mode
- Performance validation at full 500,000-rule evaluation scale
- Merchant onboarding guide and in-product setup wizard

#### Acceptance Criteria

- 20 pilot merchants successfully configure and activate auto-reordering
- Zero duplicate POs in 30-day pilot period
- Evaluation engine meets 15-minute SLA at full scale in production load test
