---
id: PRD-012
type: prd
title: Multi-Warehouse Inventory View PRD
status: approved
owner: Senior PM
created: '2024-03-23T23:37:59.496Z'
updated: '2025-10-19T12:25:25.327Z'
tags:
  - prd
  - inventory-management
summary: Multi-Warehouse Inventory View PRD
related_tdds:
  - TDD-014
  - TDD-015
example: true
related_standards:
  - STANDARD-017
---

## Summary

Extend the inventory dashboard to provide a unified, aggregated view of stock across multiple warehouses simultaneously. Currently, merchants and operations staff must check each warehouse location independently, making it impossible to quickly answer "how much total available stock do I have across all my warehouses for this SKU?" This feature enables cross-warehouse inventory optimization and simplifies routing decisions for merchants who fulfil from multiple locations.

## Goals

- Enable merchants to see total available stock across all warehouses in a single view
- Support intelligent fulfilment routing by exposing per-warehouse availability alongside aggregated totals
- Reduce time spent manually aggregating stock reports from multiple warehouse systems
- Enable inter-warehouse transfer recommendations based on distribution imbalances

## In Scope

- Aggregated stock view: total on-hand, reserved, and available per SKU across all connected warehouses
- Per-warehouse breakdown within the aggregated view (expandable row per SKU)
- Warehouse filter: select a subset of warehouses to include in aggregation
- Stock distribution heatmap: visual representation of how stock is distributed across locations
- Inter-warehouse imbalance indicators: flags SKUs where stock is heavily concentrated in one location
- CSV export of multi-warehouse aggregated view
- Merchant-level warehouse grouping: allow merchants to group warehouses (e.g., "East Coast", "West Coast")

## Out of Scope

- Automated inter-warehouse transfer initiation (separate initiative)
- Demand forecasting per warehouse region
- Warehouse capacity planning features
- Real-time 3PL cost comparison for routing decisions
- Integration with carrier routing APIs

## Users and Flows

**Multi-warehouse merchants** are the primary users. These are merchants who hold stock across 3 or more warehouse locations and need to understand their total availability before accepting large orders. A typical flow: search for a SKU, see the aggregated total available, expand the row to see the per-warehouse breakdown, and decide which warehouse to allocate the order from based on proximity to the customer.

**Fulfilment operations teams** use the view for daily allocation planning. They monitor which warehouses are running low relative to others and initiate manual transfer requests to rebalance. The inter-warehouse imbalance indicator is their primary tool for identifying rebalancing candidates.

**Internal supply chain planners** use the aggregated view for weekly stock reporting. They export CSV snapshots of the multi-warehouse view for upload to their planning tools. The warehouse grouping feature enables regional roll-ups without manual spreadsheet work.

## Requirements

- Display aggregated on-hand, reserved, and available quantities per SKU with per-warehouse breakdown available on demand
- Support aggregation across a user-selected subset of warehouses (filter by warehouse or warehouse group)
- Update aggregated totals within 15 seconds of any stock movement across any connected warehouse
- Allow merchants to create named warehouse groups (up to 20 groups, up to 50 warehouses per group)
- Flag SKUs where > 80% of available stock is concentrated in a single location
- Export aggregated multi-warehouse view to CSV (up to 100,000 rows)
- Require no more than 2 clicks to see per-warehouse breakdown from the aggregated view

## KPIs

- **Aggregation freshness**: P95 aggregated view update latency < 15s from warehouse movement event
- **Support ticket reduction**: Multi-warehouse stock inquiry tickets reduced by 50% within 90 days
- **Feature adoption**: 60% of merchants with 3+ warehouses use the multi-warehouse view weekly within 60 days
- **Export performance**: 100,000-row CSV export completes within 90 seconds

## Information Architecture

- Multi-warehouse view extends the existing inventory dashboard at `portal.example.com/inventory/multi-warehouse`
- Aggregation computed server-side by calling the Stock Level Calculator's aggregation endpoint
- Warehouse group configuration stored in the merchant portal user preferences store
- Technical design references: [[TDD-014|TDD-014]] (warehouse integration adapter) and [[TDD-015|TDD-015]] (stock reservation system)

## Data Model

- **WarehouseGroup**: `group_id`, `merchant_id`, `name`, `warehouse_ids[]` (merchant-defined grouping)
- **AggregatedStockLevel**: `sku_id`, `merchant_id`, `total_on_hand`, `total_reserved`, `total_available`, `warehouse_breakdown[]` (computed view)
- **ImbalanceIndicator**: `sku_id`, `dominant_warehouse_id`, `concentration_pct` (flagged when > 80%)

## Non-Functional

- Aggregation query must complete in < 500ms for merchants with up to 50 warehouses and 50,000 SKUs
- Warehouse group configuration changes must take effect within 1 minute
- Multi-tenant isolation: merchants can only aggregate their own warehouse connections
- CSV export must be backgrounded for large exports (> 10,000 rows) with email notification on completion

## Constraints

- Aggregation must use the Stock Level Calculator API; no direct database aggregation queries
- Warehouse group configuration limited to 20 groups and 50 warehouses per group to bound aggregation complexity
- Must support merchants with between 3 and 50 warehouses; merchants with 1-2 warehouses can use the existing per-location view

## Risks

- **Aggregation latency at 50 warehouses** may exceed 500ms for large catalogs if individual warehouse queries are not parallelized. Mitigation: Implement parallel warehouse queries with a 400ms timeout per warehouse; exclude timed-out warehouses with a visible warning.
- **Stock imbalance flag accuracy**: The 80% concentration threshold may be too aggressive for small-SKU merchants with naturally uneven distribution. Mitigation: Make the threshold configurable per merchant.
- **Warehouse group configuration complexity**: Merchants may struggle to set up groups correctly. Mitigation: Provide a wizard-style onboarding flow for group creation with example use cases.

## Milestones

### M1: Aggregated Stock View (Week 1-4)

#### Deliverables

- Aggregated on-hand, reserved, available totals per SKU across all merchant warehouses
- Per-warehouse breakdown expandable row
- Warehouse filter for subsetting the aggregation

#### Acceptance Criteria

- Aggregated total matches sum of individual warehouse quantities for 100% of tested SKUs
- Per-warehouse breakdown visible within 2 clicks from aggregated row
- Aggregation updates within 15 seconds of a simulated warehouse movement

### M2: Warehouse Groups and Imbalance Indicators (Week 5-7)

#### Deliverables

- Merchant-defined warehouse groups with named aggregation
- Stock imbalance indicator (>80% concentration flag)
- Multi-warehouse CSV export

#### Acceptance Criteria

- Merchant can create a warehouse group and see correct aggregation within 1 minute
- Imbalance flag appears for all SKUs meeting the concentration threshold in test data
- CSV export of 100,000 rows completes in < 90 seconds
