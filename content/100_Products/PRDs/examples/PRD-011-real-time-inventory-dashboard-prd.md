---
id: PRD-011
type: prd
title: Real-Time Inventory Dashboard PRD
status: approved
owner: Senior PM
created: '2025-03-08T14:23:05.177Z'
updated: '2025-09-17T12:01:38.564Z'
tags:
  - prd
  - inventory-management
summary: Real-Time Inventory Dashboard PRD
related_tdds:
  - TDD-011
  - TDD-013
example: true
related_standards:
  - STANDARD-016
---

## Summary

Build a real-time inventory dashboard that gives merchants and internal operations teams live visibility into stock levels, recent movements, and availability status across all warehouse locations. This replaces the current static inventory reports that are generated nightly and are out of date by morning.

The dashboard must reflect stock changes within 10 seconds of a warehouse movement being processed and support concurrent access by hundreds of merchants without degrading response times.

## Goals

- Give merchants real-time confidence in their stock positions to reduce over-ordering and stockout surprises
- Eliminate the daily "inventory check" support ticket category (currently ~40 tickets/week)
- Provide a foundation for future proactive alerting (low stock, reorder point) features
- Enable operations teams to diagnose sync issues and reconciliation discrepancies without engineering support

## In Scope

- Real-time on-hand, reserved, and available quantity per SKU per warehouse location
- Recent stock movement history (last 100 movements per SKU per location, rolling 30 days)
- Multi-location aggregated view (total available across all locations for a SKU)
- Stock search and filter by SKU name, barcode, category, and warehouse
- Exportable CSV snapshot of current stock levels
- Low stock indicator (configurable threshold per SKU)
- Dashboard access control: merchants see only their own SKUs; operations see all

## Out of Scope

- Automated reorder triggers (separate PRD)
- Demand forecasting and trend charts (separate PRD)
- Warehouse-to-warehouse transfer initiation from the dashboard
- Historical reporting beyond 30-day movement history
- Mobile native application (web-responsive is sufficient for v1)

## Users and Flows

**Merchants** are the primary users. They access the dashboard to check stock positions before making purchasing decisions, verify that a warehouse receipt has been processed correctly, and investigate why an order was cancelled due to zero stock. A typical merchant session involves searching for a SKU, reviewing its current stock across all locations, and spot-checking the last few movements against their expected receipt quantities.

**Operations staff** use the dashboard for broader platform health monitoring: checking for warehouses with stale sync status, investigating reconciliation discrepancies flagged by automated alerts, and responding to merchant support tickets about stock levels. They need cross-merchant visibility and per-warehouse health indicators not available to merchants.

## Requirements

- Display on-hand, reserved, and available quantity per SKU per location, refreshing within 10 seconds of a movement being processed
- Show the 100 most recent stock movements per SKU per location with timestamp, event type, delta, and source
- Support full-text search across SKU name, description, and barcode with results in < 500ms
- Aggregate available quantity across all locations for a given SKU in a single consolidated view
- Allow export of current stock snapshot to CSV (up to 50,000 rows per export)
- Display warehouse sync status (last sync time, sync lag, connection health) per warehouse
- Enforce multi-tenant data isolation: merchants can only view their own SKUs
- Configurable low-stock threshold per SKU with visual indicator when below threshold

## KPIs

- **Stock level data freshness**: P95 refresh latency < 10s from movement event to dashboard update
- **Support ticket reduction**: Low-stock and stock-level support tickets reduced by 60% within 90 days of launch
- **Merchant adoption**: 70% of active merchants access the dashboard at least once per week within 60 days
- **Search performance**: SKU search P95 < 500ms at 200 concurrent users
- **Export completion**: CSV export of 50,000 rows completes within 60 seconds

## Information Architecture

- Dashboard frontend served from the merchant portal (`portal.example.com/inventory`)
- Backend API calls the Stock Level Calculator query endpoints and SKU Registry search endpoints
- Movement history served from the Inventory Event Bus event log read API
- Operations view served from a separate internal URL with elevated permissions
- This PRD in `100_Products/PRDs/`; technical design in [[TDD-011|TDD-011]] (stock levels) and [[TDD-013|TDD-013]] (SKU search)

## Data Model

- **StockLevel**: sku_id, location_id, on_hand_qty, reserved_qty, available_qty, last_updated (read from Stock Level Calculator)
- **StockMovement**: event_id, sku_id, location_id, event_type, delta, occurred_at, source, actor (read from event log)
- **LowStockThreshold**: sku_id, merchant_id, threshold_qty (merchant-configurable, stored in dashboard settings)

## Non-Functional

- Dashboard must load within 3 seconds for a merchant's SKU list (< 10,000 SKUs)
- API rate limit: 60 requests/minute per merchant session
- Multi-tenant isolation enforced at the API level; no cross-merchant data leakage
- All dashboard access logged for audit (who viewed which SKU's stock data)
- Accessible on modern browsers (Chrome, Firefox, Safari, Edge); no IE11 support

## Constraints

- Must use existing Stock Level Calculator and SKU Registry APIs; no direct database access from the dashboard backend
- Merchant authentication handled by existing portal session management
- Operations access uses existing internal SSO
- No new cloud services without platform team approval

## Risks

- **Stock level cache staleness** during the 10-second refresh window could confuse merchants about precision. Mitigation: Display "last updated" timestamp prominently so merchants understand data freshness.
- **High-SKU merchant performance**: Merchants with 100,000+ SKUs may experience slow initial loads. Mitigation: Paginate the SKU list, lazy-load stock levels on scroll, and test with the largest merchant catalog in load testing.
- **Warehouse sync status misleads merchants**: If a warehouse is temporarily offline, showing stale stock levels without context creates confusion. Mitigation: Show a clear warning banner when warehouse sync lag exceeds 2 minutes.

## Milestones

### M1: Core Stock View (Week 1-4)

#### Deliverables

- SKU list with on-hand, reserved, available quantities per location
- Stock movement history (last 100 events per SKU/location)
- Single-location and aggregated multi-location views
- Multi-tenant data isolation enforced

#### Acceptance Criteria

- Merchant can log in and see their current stock levels within 10 seconds of actual movement
- Movement history matches event log for a sample of 20 SKUs
- Merchant A cannot see Merchant B's stock data

### M2: Search, Export, and Operations View (Week 5-7)

#### Deliverables

- Full-text SKU search with filter by warehouse and category
- CSV export for up to 50,000 rows
- Operations view with cross-merchant visibility and warehouse health indicators

#### Acceptance Criteria

- SKU search returns relevant results in < 500ms for a 500,000-SKU catalog
- CSV export of 50,000 rows completes in < 60 seconds
- Operations team can view stock for all merchants and see per-warehouse sync status

### M3: Low Stock Alerts and Production Launch (Week 8-10)

#### Deliverables

- Configurable low-stock threshold per SKU with dashboard indicator
- Performance validation at 200 concurrent users
- Merchant onboarding documentation and in-product tooltips

#### Acceptance Criteria

- Low-stock indicator displays correctly for all SKUs below their configured threshold
- Dashboard load time < 3 seconds at 200 concurrent merchant sessions
- 5 pilot merchants confirm dashboard meets their daily workflow needs
