---
id: PRD-014
type: prd
title: Inventory Forecasting Tool PRD
status: approved
owner: Head of Product
created: '2024-09-24T17:15:09.186Z'
updated: '2026-07-05T17:42:04.902Z'
tags:
  - prd
  - inventory-management
summary: Inventory Forecasting Tool PRD
related_tdds:
  - TDD-011
  - TDD-012
example: true
related_standards:
  - STANDARD-013
---

## Summary

Build an inventory forecasting tool that uses historical stock movement data to project future stock depletion dates and recommend optimal reorder timing. This gives merchants proactive visibility into how long their current stock will last based on recent sales velocity, reducing both stockouts (ordering too late) and overstock (ordering too early). The forecasting model draws on stock event history provided by [[TDD-012|TDD-012]] and current stock levels from [[TDD-011|TDD-011]].

## Goals

- Help merchants predict stockout dates based on recent sales velocity, reducing stockout incidents by 30%
- Reduce overstock purchasing by surfacing SKUs with low velocity that are unlikely to sell out before their next planned reorder
- Provide actionable reorder timing recommendations that account for supplier lead times
- Give operations teams aggregate visibility into platform-wide stock health trends

## In Scope

- Velocity-based depletion forecast: days of stock remaining per SKU based on 7, 14, and 30-day rolling average velocity
- Projected stockout date per SKU per warehouse location
- Reorder timing recommendation: "Order by [date] to avoid stockout given [lead time] days"
- Seasonality adjustment: uplift/downlift velocity based on historical seasonal patterns (where sufficient history exists)
- Low-velocity flag: identify SKUs with < 1 unit/day average that are overstocked relative to forecast
- Trend direction indicator: whether velocity is increasing, stable, or decreasing over the last 30 days
- Forecast accuracy tracking: how close previous forecasts were to actual depletion dates

## Out of Scope

- Machine learning demand sensing (phase 2)
- Promotional uplift modelling
- Competitor stock visibility
- Automated purchasing based on forecasts (see Automated Reorder System PRD)
- Customer-level demand segmentation
- Raw stock movement data export for external analytics tools

## Users and Flows

**Merchants** use the forecasting tool as part of their weekly purchasing review. They open the forecast view, sort by "days of stock remaining" ascending to find their most at-risk SKUs, review the reorder timing recommendations for those SKUs, and initiate purchase orders. The tool removes the manual spreadsheet velocity calculations merchants currently do to decide when to reorder.

**Head of inventory / operations leads** use the aggregate view to assess platform-wide stock health. They look for clusters of SKUs approaching stockout to flag for the merchant success team, and review overstock indicators to identify candidates for promotions or returns to suppliers.

## Requirements

- Compute and display days-of-stock-remaining for each active SKU using configurable velocity window (7, 14, or 30-day rolling average)
- Display projected stockout date based on current available quantity and average daily velocity
- Show reorder timing recommendation: "Order by [date]" computed as stockout_date minus configured supplier lead time
- Flag SKUs with less than 14 days of stock remaining with a configurable warning threshold
- Flag SKUs with velocity < 0.1 units/day that have more than 180 days of stock as overstocked
- Display velocity trend direction (increasing/stable/decreasing) for each SKU
- Refresh forecasts hourly based on the most recent 24-hour stock movements
- Support filtering by warehouse, category, and SKU to narrow the forecast view
- Allow merchants to override the computed velocity with a manual velocity estimate for special situations

## KPIs

- **Forecast accuracy**: Average absolute forecast error < 15% for days-of-stock-remaining within a 7-day horizon
- **Stockout reduction**: Stockouts for merchants using the tool reduced by 30% vs baseline within 90 days
- **Merchant adoption**: 50% of eligible merchants review their forecast weekly within 60 days
- **Overstock identification**: 10% reduction in average days-of-stock on hand across the merchant base within 6 months

## Information Architecture

- Forecasting tool accessible at `portal.example.com/inventory/forecast`
- Velocity computation service reads from the stock event history provided by the Inventory Sync Pipeline ([[TDD-012|TDD-012]])
- Current stock levels read from the Stock Level Calculator ([[TDD-011|TDD-011]])
- Forecasts stored in a dedicated forecast table (refreshed hourly by a background job)
- Merchant lead time and velocity override settings stored in the merchant preferences store

## Data Model

- **VelocityMetric**: `sku_id`, `location_id`, `merchant_id`, `avg_daily_units_7d`, `avg_daily_units_14d`, `avg_daily_units_30d`, `trend_direction`, `computed_at`
- **StockForecast**: `sku_id`, `location_id`, `merchant_id`, `available_qty`, `days_remaining_30d`, `projected_stockout_date`, `reorder_by_date`, `lead_time_days`, `overstock_flag`, `low_stock_flag`, `updated_at`
- **VelocityOverride**: `sku_id`, `merchant_id`, `override_daily_units`, `set_by`, `valid_until`

## Non-Functional

- Forecast refresh for a merchant with 50,000 SKUs must complete within 30 minutes of the hourly trigger
- Forecasting page must load within 3 seconds for a merchant with 10,000 active SKUs
- Velocity computation must handle gaps in the event log gracefully (sparse data for slow-moving SKUs)
- Forecast data retained for 12 months to support forecast accuracy retrospectives

## Constraints

- Initial velocity model is a simple rolling average; no ML framework dependencies in v1
- Seasonality adjustment only available for SKUs with at least 12 months of event history
- Forecast must be clearly labelled as a projection, not a guarantee; legal review required before launch
- Must use existing event log and stock level APIs; no new data pipeline infrastructure

## Risks

- **New SKU forecast accuracy**: SKUs with less than 7 days of history will have unreliable forecasts. Mitigation: Flag new SKUs as "insufficient history" rather than displaying a potentially misleading forecast.
- **Velocity computed on highly irregular SKUs** (e.g., bulk orders every 6 months) will produce unhelpful forecasts. Mitigation: Flag SKUs with high coefficient of variation as "irregular demand" and suggest manual planning.
- **Forecast staleness if hourly refresh fails**: Merchants could make decisions on stale data. Mitigation: Display "forecast last updated" timestamp prominently; alert operations if refresh fails for > 4 hours.

## Milestones

### M1: Velocity Computation and Basic Forecast (Week 1-5)

#### Deliverables

- Velocity computation service (7d, 14d, 30d rolling averages)
- Days-of-stock-remaining and projected stockout date
- Forecast table populated hourly for all active SKUs
- Basic forecast view in merchant portal

#### Acceptance Criteria

- Velocity figures for a sample of 20 SKUs match manual calculations from event log data
- Forecast view loads within 3 seconds for 10,000-SKU merchant
- Hourly refresh completes within 30 minutes for a 50,000-SKU merchant in load test

### M2: Reorder Recommendations and Overstock Flags (Week 6-8)

#### Deliverables

- Reorder timing recommendation using configurable supplier lead time
- Overstock and low-stock flags with configurable thresholds
- Trend direction indicator
- Velocity override per SKU

#### Acceptance Criteria

- Reorder recommendations accurately account for merchant-configured lead times
- Overstock and low-stock flags match expected flags for a set of test scenarios
- Merchant can override velocity and see reorder recommendation update immediately
