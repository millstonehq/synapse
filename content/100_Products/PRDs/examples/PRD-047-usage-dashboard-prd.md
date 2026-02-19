---
id: PRD-047
type: prd
title: Usage Dashboard PRD
status: approved
owner: Product Manager
created: '2025-01-25T05:03:42.342Z'
updated: '2025-12-23T01:02:28.384Z'
tags:
  - prd
  - billing-engine
summary: Usage Dashboard PRD
related_tdds:
  - TDD-046
  - TDD-047
example: true
related_standards:
  - STANDARD-055
---

## Summary

Build a Usage Dashboard that gives customers real-time visibility into their consumption of metered billing metrics — API calls, active seats, processed records, and data storage — within their current billing period. Customers with usage-based pricing have consistently cited lack of usage visibility as a top driver of billing disputes and surprise invoices. This dashboard is the primary customer-facing view of the data produced by the Invoice Generation Pipeline ([[TDD-046|TDD-046]]) and the Usage Aggregation Service ([[TDD-047|TDD-047]]). Compliance requirements are governed by [[STANDARD-055|STANDARD-055]].

## Goals

- Eliminate "surprise invoice" billing disputes by giving customers advance visibility into accruing charges
- Reduce billing-related support tickets for usage-based plan customers by 40%
- Increase adoption of usage-based pricing plans by removing the opacity that drives customer reluctance
- Enable customers to self-manage their usage relative to plan thresholds and upgrade proactively

## In Scope

- Current-period usage summary by metric with trend vs prior period
- Historical usage chart (daily bars for current and previous 2 billing periods)
- Estimated current-period invoice amount based on accrued usage
- Per-metric breakdown showing usage, unit price, and accrued charge
- Usage data export (CSV) for the last 3 billing periods
- Email alert when usage exceeds 80% of plan limit (configurable threshold)

## Out of Scope

- Real-time usage (sub-minute latency) — dashboard shows hourly aggregates with up to 2-hour lag
- Usage analytics beyond 12 months of history
- Team-member-level usage breakdown (aggregate account level only in this release)
- In-app usage budget caps or hard limits

## Users and Flows

**Account admin on usage-based plan**: The primary user. They check the dashboard at the start of each week to assess whether usage is on track for the billing period. They use the estimated invoice amount to decide whether to optimize usage or upgrade to a higher tier before the period ends.

**Finance staff**: Accesses the dashboard at the end of each month before the invoice arrives to validate expected charges and prepare for internal budget reconciliation. Uses the CSV export to import data into their finance system.

## Requirements

- Display current-period start and end dates and days remaining
- Show current-period usage total for each metered metric with units (calls, seats, GB, records)
- Show prior-period usage for each metric for direct comparison
- Show estimated current-period invoice amount with line-item breakdown by metric
- Render daily usage bar chart for the current period and prior 2 periods for each metric
- Provide CSV export of daily usage data for the last 3 billing periods
- Send email alert when usage crosses 80% of any plan limit (user-configurable, default on)
- Refresh dashboard data at most every 2 hours from Usage Aggregation Service

## KPIs

- **Dispute reduction**: Billing disputes from usage-based plan customers decrease by 40% within 3 months of launch
- **Dashboard engagement**: 50% of usage-based plan customers view the dashboard at least once per billing cycle within 6 months
- **Alert engagement**: 30% of customers who receive an 80% threshold alert take action (upgrade, optimize) before billing period ends
- **CSV export usage**: 20% of enterprise customers use CSV export each month

## Information Architecture

- Dashboard UI lives at `app.example.com/billing/usage`
- Usage data sourced from Usage Aggregation Service REST API
- Invoice estimates calculated by calling Invoice Generation Pipeline preview endpoint
- TDD for Invoice Generation Pipeline: [[TDD-046|TDD-046]]
- TDD for Usage Aggregation Service: [[TDD-047|TDD-047]]
- Compliance requirements: [[STANDARD-055|STANDARD-055]]

## Data Model

- **UsageSummaryView**: Computed view — `customer_id`, `metric_name`, `current_period_quantity`, `prior_period_quantity`, `unit_price`, `accrued_charge_cents`, `plan_limit` (nullable)
- **UsageDailyPoint**: `customer_id`, `metric_name`, `date`, `quantity` (read from aggregation service, not stored separately)
- **UsageAlertPreference**: `customer_id`, `metric_name`, `threshold_pct` (default 80), `email_enabled`, `updated_at`

## Non-Functional

- Dashboard data must be no more than 2 hours stale; staleness indicator shown in UI if data is older
- CSV export must complete within 10 seconds for 3 months of daily data
- Dashboard page must load in under 3 seconds (P95) including all metric charts
- Usage data is read-only in this feature; no writes to the aggregation service from the dashboard

## Constraints

- Usage data must be sourced from the Usage Aggregation Service API — no direct database reads from the dashboard backend
- Email alerts must use the existing notification service, not a new email delivery mechanism
- Budget: 2 engineers + 1 designer for 6 weeks

## Risks

- **2-hour data lag causes customer confusion** if they expect real-time data. Mitigation: prominently display "Last updated X minutes ago" timestamp on the dashboard; add FAQ explaining aggregation lag.
- **Estimated invoice amount diverges from actual invoice** due to mid-period plan changes or proration. Mitigation: display estimate as "approximate" with a disclaimer and link to the proration explanation wiki.
- **Usage Aggregation Service availability becomes a blocker** for the dashboard. Mitigation: cache the last successful response in Redis with a 4-hour TTL; show stale indicator rather than error page.

## Milestones

### M1: Current Usage Summary and Charts (Week 1-4)

#### Deliverables

- Current-period usage summary by metric (quantity, unit price, accrued charge)
- Daily usage bar chart for current and prior 2 periods
- Estimated invoice amount with line-item breakdown
- Prior-period comparison column

#### Acceptance Criteria

- Usage data matches Usage Aggregation Service output within 2-hour window
- Charts render for all 4 metric types (API calls, seats, records, storage)
- Estimated invoice amount matches Invoice Pipeline preview within $0.01

### M2: Export and Alerts (Week 5-6)

#### Deliverables

- CSV export for last 3 billing periods
- 80% threshold email alert with user preference toggle
- Usage alert preference settings page

#### Acceptance Criteria

- CSV export includes daily usage for all metrics for the last 3 billing periods
- Alert email is sent within 30 minutes of usage crossing the threshold
- User can disable alerts per metric from the settings page
