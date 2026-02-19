---
id: PRD-050
type: prd
title: Revenue Forecasting Tool PRD
status: approved
owner: Senior PM
created: '2024-09-17T23:58:22.592Z'
updated: '2025-07-06T13:46:18.848Z'
tags:
  - prd
  - billing-engine
summary: Revenue Forecasting Tool PRD
related_tdds:
  - TDD-047
  - TDD-050
example: true
related_standards:
  - STANDARD-057
---

## Summary

Build an internal Revenue Forecasting Tool that enables Finance and leadership to project monthly recurring revenue (MRR), annual recurring revenue (ARR), and usage-based revenue for the next 3 to 12 months using live billing data. The current forecasting process relies on a manually maintained spreadsheet that Finance updates each month — it does not incorporate real-time churn signals, mid-period plan changes, or usage growth trends. This tool integrates with the Usage Aggregation Service ([[TDD-047|TDD-047]]) and Billing Webhook Processor ([[TDD-050|TDD-050]]) to source live billing signals. Output formatting requirements are governed by [[STANDARD-057|STANDARD-057]].

## Goals

- Replace the manually maintained forecast spreadsheet with a live-data tool that eliminates the monthly update burden
- Improve forecast accuracy by incorporating real-time churn signals and usage growth rates
- Enable scenario planning (optimistic/base/pessimistic) for quarterly board presentations
- Provide department-level revenue attribution to support Sales and CS quota planning

## In Scope

- MRR and ARR dashboard with month-over-month trend
- 3-month, 6-month, and 12-month revenue projections based on current cohort data
- Churn rate calculation using subscription cancellation data
- New business and expansion revenue attribution (new subscriptions vs upgrades vs usage growth)
- Scenario modeling: base case, 10% better, 10% worse
- Export to CSV for Finance and board presentation use
- Integration with live billing data (updated daily)

## Out of Scope

- Integration with CRM pipeline data (Sales-sourced revenue forecasting)
- Per-customer-level revenue forecasting
- Real-time (sub-daily) data updates
- Automated board presentation generation

## Users and Flows

**VP of Finance**: Primary user. Reviews the dashboard at the start of each week to monitor MRR trajectory, compare actual vs forecast, and prepare for board meetings. Uses scenario modeling to build the optimistic/pessimistic range for quarterly presentations. Exports the data to import into the board deck template.

**Head of Sales**: Uses the expansion revenue view to understand how much revenue is coming from plan upgrades vs new logos, which informs Sales team quota and hiring decisions.

## Requirements

- Display current month MRR and ARR with month-over-month change (absolute and percentage)
- Calculate and display new business MRR, expansion MRR, and churned MRR (MRR movement report)
- Project MRR for the next 12 months using a time-series model based on the last 6 months of MRR movements
- Allow user to adjust churn rate and growth rate assumptions for scenario modeling
- Show three scenarios simultaneously: base case (model-predicted), optimistic (+10% growth, -2% churn), pessimistic (-10% growth, +2% churn)
- Display a 24-month historical MRR chart alongside the 12-month projection
- Export the MRR movement report and projection as CSV
- Update all calculations daily using the previous day's billing data as the input

## KPIs

- **Forecast accuracy**: 12-month forward MRR projection is within 15% of actual MRR when measured at the end of the projection period
- **Manual update elimination**: Finance no longer maintains a manual spreadsheet (measured by Finance team sign-off at 3 months post-launch)
- **Time savings**: Monthly forecast preparation time decreases from 8 hours to under 1 hour
- **Adoption**: Finance and leadership access the tool at least weekly within 2 months of launch

## Information Architecture

- Forecasting tool hosted at `admin.example.com/billing/forecast` (internal, VPN-required)
- Revenue data sourced from Billing Engine double-entry ledger (daily batch read)
- Subscription data sourced from Subscription Management Service
- TDD: [[TDD-047|TDD-047]] (Usage Aggregation), [[TDD-050|TDD-050]] (Webhook Processor)
- Output formatting: [[STANDARD-057|STANDARD-057]]

## Data Model

- **MRRSnapshot**: `date`, `new_mrr_cents`, `expansion_mrr_cents`, `reactivation_mrr_cents`, `churned_mrr_cents`, `contraction_mrr_cents`, `net_new_mrr_cents`, `total_mrr_cents`
- **RevenueForecast**: `generated_at`, `scenario` (base/optimistic/pessimistic), `forecast_month`, `projected_mrr_cents`, `model_version`
- **ScenarioAssumption**: `forecast_id`, `churn_rate_pct`, `growth_rate_pct`, `expansion_rate_pct`

## Non-Functional

- Dashboard must load in under 3 seconds
- Daily data refresh job must complete before 08:00 UTC so Finance sees current data at the start of the business day
- Forecast model must be explainable — show the assumptions and input data used for each projection in the UI
- Historical data must be retained for at least 5 years

## Constraints

- Revenue data must be sourced from the internal double-entry ledger — not directly from Stripe
- Forecast model must be deterministic for a given snapshot date (same input = same output for audit purposes)
- Budget: 2 engineers + 1 data analyst for 8 weeks

## Risks

- **Forecast model accuracy is poor in early months** when there is limited subscription history. Mitigation: use at least 6 months of data before publishing MRR projections; show a "limited history" warning until 6 months of data exists.
- **Usage-based revenue is harder to forecast** than flat-rate MRR. Mitigation: forecast usage revenue separately using usage growth trends and clearly label it as "usage revenue estimate" with higher uncertainty range.

## Milestones

### M1: MRR Dashboard and Historical Data (Week 1-4)

#### Deliverables

- MRR movement report (new/expansion/churn/contraction breakdown) for last 12 months
- Total MRR and ARR with month-over-month change
- 24-month historical MRR chart
- Daily data refresh pipeline

#### Acceptance Criteria

- MRR totals match Finance's manually calculated figures for the last 3 months within 1%
- Daily refresh completes before 08:00 UTC in staging environment
- Chart renders correctly for all 24 historical months

### M2: Projections, Scenarios, and Export (Week 5-8)

#### Deliverables

- 12-month MRR projection (base case)
- Optimistic and pessimistic scenario views
- User-adjustable churn and growth rate assumptions
- CSV export for projection and MRR movement report

#### Acceptance Criteria

- Three scenarios display simultaneously with visible assumption differences
- User can adjust churn rate by +/- 5% and see projection update in under 1 second
- CSV export contains all required fields per [[STANDARD-057|STANDARD-057]]
