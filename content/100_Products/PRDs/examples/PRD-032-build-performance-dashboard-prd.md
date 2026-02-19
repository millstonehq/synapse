---
id: PRD-032
type: prd
title: Build Performance Dashboard PRD
status: proposed
owner: Product Manager
created: '2025-08-04T16:03:27.834Z'
updated: '2025-11-03T11:57:16.335Z'
tags:
  - prd
  - ci-cd-platform
summary: Build Performance Dashboard PRD
related_tdds:
  - TDD-035
  - TDD-033
example: true
related_standards:
  - STANDARD-038
---

## Summary

Provide engineers and engineering managers with a centralized dashboard showing build pipeline performance metrics across all services. Currently, build performance data is scattered across GitHub Actions logs, Prometheus metrics, and ad-hoc queries. Slow builds are noticed only when individual engineers complain; there is no systematic way to identify which services have regressed, which teams have the most room for improvement, or whether platform-level changes (new runner images, cache improvements) are having the expected impact. This dashboard makes CI build health visible and actionable.

## Goals

- Make build performance visible at the service and team level so that regressions are detected within 24 hours
- Identify the top 5 slowest services each week and surface them to engineering managers
- Measure the impact of platform-level CI improvements (cache tuning, runner upgrades) with before/after comparisons
- Reduce average build time from 12 minutes to under 7 minutes across the fleet within 2 quarters of launch

## In Scope

- Per-service build time trends (P50, P95, min, max over rolling 7/30/90-day windows)
- Cache hit rate per service and fleet-wide
- Build failure rate and common failure categories (test failures, lint, build errors)
- Runner utilization and queue wait time
- Top 10 slowest services ranked by P95 build time
- Comparison view showing before/after build times around a specified date

## Out of Scope

- Individual build log viewer (engineers use GitHub Actions UI for this)
- Test result tracking or flaky test detection (separate initiative)
- Cost attribution per service (in scope for the CI/CD Infrastructure Cost reporting initiative)
- Non-GitHub Actions CI systems

## Users and Flows

**Individual engineers** use the per-service view to check whether a recent Dockerfile or dependency change caused a build time regression. They navigate to their service, look at the 7-day trend, and compare before/after a specific commit date using the comparison view.

**Engineering managers** use the fleet-wide view during weekly planning to identify which teams have the slowest builds and whether the overall fleet average is improving. They share the top-10-slowest list with team leads as a prioritization input.

**Platform engineers** use the dashboard to measure the impact of changes they ship: runner image updates, build cache configuration changes, Dockerfile template updates. The comparison view lets them show a clear before/after against a deploy date.

## Requirements

- Collect build duration, cache hit/miss, and outcome (success/failure) per build from GitHub Actions API
- Store at least 90 days of build history per service
- Display P50 and P95 build time trends as line charts with configurable time windows (7/30/90 days)
- Show a ranked list of services by P95 build time, filterable by team or tag
- Cache hit rate displayed as a percentage with weekly trend sparkline
- Comparison view: user selects a before date and after date; dashboard shows side-by-side metric cards
- Refresh data every 15 minutes; display last-updated timestamp on each view
- Allow engineers to filter by branch (main vs feature branches)

## KPIs

- **Average fleet P95 build time**: Target < 7 minutes within 2 quarters of dashboard launch
- **Cache hit rate**: Target > 70% fleet-wide (currently ~41% after regression)
- **Regression detection time**: New build time regressions identified within 24 hours via automated alert
- **Dashboard adoption**: > 80% of engineering teams have at least one member using the dashboard weekly within 60 days of launch

## Information Architecture

- Technical design in `90_Architecture/TDDs/` (see [[TDD-035|TDD-035]] and [[TDD-033|TDD-033]])
- Build pipeline optimization context in `75_Wikis/` (WIKI-027)
- This PRD in `100_Products/PRDs/`

## Data Model

- **BuildRecord**: `id`, `service_name`, `team`, `branch`, `commit_sha`, `run_id`, `duration_ms`, `outcome`, `cache_hit`, `runner_type`, `started_at`
- **BuildAggregation**: Precomputed daily/weekly rollup: `service_name`, `date`, `p50_ms`, `p95_ms`, `cache_hit_rate`, `success_rate`, `build_count`
- **ServiceMetadata**: `service_name`, `team`, `tags` — sourced from the service catalog for filtering

## Non-Functional

- Dashboard page load under 2 seconds for a service with 90 days of history
- Build data ingestion lag must not exceed 15 minutes from GitHub Actions completion
- Historical data retained for a minimum of 1 year
- No authentication required for read access within the internal network; dashboard is informational only

## Constraints

- Must use GitHub Actions API as the data source; no changes to CI workflows required from service teams
- Must run on existing Kubernetes infrastructure; no new cloud services
- Must use the existing Grafana instance for charts; no standalone frontend framework

## Risks

- **GitHub Actions API rate limits** may restrict data collection during peak hours. Mitigation: use conditional requests (ETags) and stagger collection jobs across services.
- **Data freshness complaints** if 15-minute refresh feels stale. Mitigation: display last-updated prominently; provide a manual refresh button that triggers an immediate pull for a single service.
- **Scope creep to flaky test detection** is likely given adjacency to build health. Mitigation: explicitly out of scope; document the boundary clearly and create a separate backlog item.

## Milestones

### M1: Data Collection and Storage (Weeks 1-3)

#### Deliverables

- GitHub Actions API collector running on 15-minute interval for all services
- BuildRecord storage in PostgreSQL with 90-day retention
- Daily aggregation job producing BuildAggregation rows

#### Acceptance Criteria

- Build data for all services is collected within 15 minutes of job completion
- Aggregation job runs nightly and produces correct P50/P95 values (verified against raw records)
- 30 days of back-fill complete for all services

### M2: Dashboard Views (Weeks 4-6)

#### Deliverables

- Per-service trend view (P50/P95 line chart, cache hit rate, failure rate)
- Fleet-wide ranked list of slowest services
- Comparison view with before/after date selector

#### Acceptance Criteria

- Per-service page loads within 2 seconds for a service with 90 days of data
- Ranked list correctly orders services by P95 build time
- Comparison view shows statistically accurate before/after for a test service with known regression date
