---
id: PRD-040
type: prd
title: Cost-Aware Monitoring Configuration PRD
status: draft
owner: Senior PM
created: '2025-09-05T07:04:42.248Z'
updated: '2025-07-15T19:13:43.529Z'
tags:
  - prd
  - monitoring-stack
summary: Cost-Aware Monitoring Configuration PRD
related_tdds:
  - TDD-039
  - TDD-038
example: true
related_standards:
  - STANDARD-045
---

## Summary

Build a cost-aware monitoring configuration system that shows teams the storage cost implications of their metric cardinality, dashboard query patterns, and retention settings before those choices are committed to production. As documented in REPORT-063, the monitoring platform is 7.9% over the monthly infrastructure budget, with ScyllaDB costs growing 28% year-over-year. This product makes cost visible and actionable at the point of configuration, rather than as a lagging report.

## Goals

- Surface real-time storage cost estimates when teams configure new metrics or extend retention
- Identify and rank the top cost contributors (by service, by metric name, by dashboard query)
- Enable teams to self-optimize their monitoring footprint without Monitoring Engineering involvement

## In Scope

- Metric cardinality cost estimator (cost per label combination per month)
- Dashboard query cost analyzer: identifies high-egress queries and suggests recording rule alternatives
- Retention policy self-service with cost impact preview
- Monthly cost attribution report per team/service
- Integration with [[TDD-038|Metric Aggregation Pipeline]] for recording rule recommendations
- Dashboard cost annotations in the dashboard builder ([[TDD-039|TDD-039]])

## Out of Scope

- Automatic cost remediation (recommendations only; teams action them)
- Cross-cloud cost optimization (single provider only)
- Log pipeline cost management (separate initiative)
- Chargeback billing (cost visibility only, no internal billing)

## Users and Flows

**Service engineers** see cost impact when they add new metric labels or create new dashboards. The flow: engineer adds a new label to a metric → cardinality estimator shows "this label adds ~$47/month" → engineer decides whether the label is worth the cost → if not, they remove it before deploying.

**Team leads** use the monthly cost attribution report to understand their team's monitoring spend and identify top cost drivers. They can drill down from "team total" to "metric name" to "specific label combination."

**Monitoring engineers** use the cost analyzer to run platform-wide cost optimization audits and identify quick wins (e.g., high-cardinality metrics from retired services still generating costs).

## Requirements

- Real-time cardinality cost estimate when a new metric label is added (estimate displayed within 3 seconds)
- Dashboard query cost score: classify queries as green/amber/red based on estimated data scanned per render
- Recording rule recommendation: for amber/red dashboard queries, suggest the equivalent recording rule expression
- Per-team cost attribution report: monthly breakdown by service, metric family, and storage tier
- Self-service retention policy editor with before/after cost comparison
- Cost annotations on dashboard panels (per-panel estimated query cost) via [[TDD-039|dashboard builder integration]]

## KPIs

- **Budget compliance**: Monitoring platform returns within 5% of monthly budget within 6 months of launch (per [[STANDARD-045|STANDARD-045]] monitoring standards)
- **Dashboard query optimization**: 60% of amber/red queries replaced with recording rules within 90 days of launch
- **Team adoption**: 80% of service teams access their cost attribution report at least monthly

## Information Architecture

- PRD (this document): `100_Products/PRDs/`
- Metric aggregation and recording rules: TDD-038 (Metric Aggregation Pipeline)
- Dashboard builder integration: TDD-039 (Custom Dashboard Builder)

## Data Model

- **MetricCostEstimate**: metric_name, label_count, estimated_series, estimated_monthly_cost_usd
- **QueryCostScore**: dashboard_uid, panel_id, query_expr, estimated_bytes_scanned, cost_tier
- **TeamCostAttribution**: team, month, total_cost_usd, top_metrics[] (name, cost_usd)
- **RetentionPolicy**: service, metric_pattern, retention_days, current_cost_usd, projected_cost_usd

## Non-Functional

- Cardinality cost estimates must return within 3 seconds (interactive, used during configuration)
- Cost attribution report computation must complete within 5 minutes for any team
- Cost data must be accurate to within 10% of actual infrastructure costs
- System must not impact real-time metric ingestion (cost computation is read-only and async)

## Constraints

- Must use the Metric Aggregation Pipeline (TDD-038) as the data source for recording rule cost comparisons
- Cost estimates are based on ScyllaDB storage pricing model; must be updated if storage vendor changes
- No new data stores — cost data is derived from existing metric metadata

## Risks

- **Inaccurate cost estimates** cause teams to distrust the tool. Mitigation: validate estimates against actual invoices monthly; publish accuracy metrics prominently.
- **Teams optimize for cost at the expense of observability**. Mitigation: cost recommendations include minimum viable coverage guidance; system warns if a team removes alerting-relevant metrics.

## Milestones

### M1: Cardinality Estimator and Attribution Report (Weeks 1-4)
#### Deliverables
- Metric cardinality cost estimator API
- Per-team monthly cost attribution report
- Retention policy editor with cost preview

#### Acceptance Criteria
- Cost estimate for a new metric label returns within 3 seconds
- Cost attribution report matches actual ScyllaDB storage costs within 10%

### M2: Dashboard Query Cost Analyzer (Weeks 5-7)
#### Deliverables
- Dashboard query cost scoring integrated into dashboard builder
- Recording rule recommendations for amber/red queries
- Cost annotations on dashboard panels

#### Acceptance Criteria
- All dashboard panels display a cost tier indicator (green/amber/red)
- Recording rule recommendations are valid PromQL expressions that reduce query cost by at least 50%
