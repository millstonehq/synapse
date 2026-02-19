---
id: PRD-024
type: prd
title: Search Analytics Dashboard PRD
status: approved
owner: Head of Product
created: '2024-08-10T21:51:19.624Z'
updated: '2026-10-16T08:49:39.879Z'
tags:
  - prd
  - search-platform
summary: Search Analytics Dashboard PRD
related_tdds:
  - TDD-023
  - TDD-025
example: true
related_standards:
  - STANDARD-026
---

## Summary

Build a self-serve search analytics dashboard that gives product managers, content operators, and search engineers visibility into search quality, user behavior, and content performance. The dashboard covers query volume trends, CTR by content type, zero-result rate, top queries, and facet usage. It is powered by the analytics pipeline in [[TDD-023|TDD-023]] and facet data from [[TDD-025|TDD-025]].

## Goals

- Give product and content teams self-serve access to search performance data without engineering involvement
- Reduce time-to-insight for search quality issues from 2 days (ad-hoc query) to 15 minutes (dashboard)
- Enable data-driven decisions for content strategy based on search demand signals

## In Scope

- Daily and hourly query volume trends
- Overall CTR, position-1 CTR, and zero-click rate over time
- Zero-result rate by query term and by content category
- Top 100 queries by volume with their CTR, zero-result rate, and position distribution
- Facet usage: which facet dimensions are most frequently applied, and which values are most popular
- Search quality metrics: NDCG@10 trend (weekly), MRR trend (weekly)
- Filter and date range controls (7-day, 30-day, custom range)
- CSV export for all tables
- Compliance with [[STANDARD-026|STANDARD-026]] for any new API endpoints

## Out of Scope

- Real-time (sub-minute) dashboard updates
- Per-user search history analysis (privacy scope)
- A/B experiment result tracking (separate tooling)
- Paid advertising or sponsored result analytics

## Users and Flows

**Product managers** use the dashboard to monitor search health and identify trends. They check the zero-result rate trend weekly to confirm that content gaps are being addressed by the content team. They export the top queries CSV to share with stakeholders.

**Content operators** use the top-queries table to identify high-volume queries with poor CTR, signaling opportunities to publish or improve content. They filter by content category to focus on their area of ownership.

**Search engineers** use the NDCG and MRR trend charts to validate relevance changes after model updates or configuration changes. They look for correlations between deployment dates and metric shifts.

## Requirements

- Dashboard data refreshes every 15 minutes from the OpenSearch analytics index
- All metrics are filterable by content category and date range
- Top queries table shows: query text, volume, CTR, zero-result rate, avg position of first click
- Zero-result rate drill-down shows: specific query terms with zero results, volume, frequency trend
- NDCG@10 trend chart shows weekly computed values with deployment event overlays
- CSV export available for top queries and zero-result queries
- Dashboard accessible to all company employees with SSO login
- [[STANDARD-026|STANDARD-026]] compliance for the dashboard API backend

## KPIs

- **Time-to-insight**: Target < 15 minutes for product managers to find the top zero-result queries
- **Dashboard usage**: Target > 20 unique active users/week within 60 days of launch
- **Data freshness**: All metrics within 15 minutes of real-time

## Information Architecture

- Backend: OpenSearch `search-events-*` and `search-signals-*` indices (from TDD-024 pipeline)
- Frontend: Internal web app using Kibana as the dashboard framework
- Permissions: Read-only access for all employees; export permission for PM role

## Data Model

- **QueryMetricRecord**: query term, time bucket, impressions, clicks, zero_results — aggregated from SearchEvent
- **FacetUsageRecord**: facet_id, value, application_count, result_count — aggregated from FacetedSearchEvent
- **QualityMetricRecord**: NDCG@10, MRR, computed_at — written by weekly batch aggregation job

## Non-Functional

- Dashboard page load within 3 seconds (pre-aggregated data, not live Elasticsearch queries)
- Metric aggregations computed in batch and stored in pre-aggregated form to avoid dashboard queries hitting the search cluster
- Data retained in the analytics store for 90 days (hot) and 1 year (cold) per OpenSearch ISM policy

## Constraints

- Dashboard must be built on Kibana to leverage existing OpenSearch cluster
- Must not add query overhead to the production Elasticsearch search cluster
- PII: no individual user identifiers stored or displayed (all analytics are aggregate)

## Risks

- **Data pipeline delay** could cause dashboard to show stale metrics. Mitigation: 15-minute refresh + staleness indicator when data is > 30 minutes old.
- **High cardinality of query terms** could make the top-queries table slow. Mitigation: pre-aggregate top 10,000 queries daily; dashboard never runs live terms aggregations.

## Milestones

### M1: Data Pipeline and Core Metrics (Weeks 1-4)

#### Deliverables

- Pre-aggregation jobs producing QueryMetricRecord and FacetUsageRecord
- Kibana dashboards for query volume, CTR, and zero-result rate
- CSV export functional

#### Acceptance Criteria

- Dashboard data within 15 minutes of real-time
- Top queries table loads in under 3 seconds

### M2: Quality Metrics and GA (Weeks 5-7)

#### Deliverables

- NDCG@10 and MRR weekly trend charts
- Deployment event overlays on quality charts
- SSO access configured for all employees

#### Acceptance Criteria

- > 10 unique users in first week post-launch
- Zero-result drill-down identifies actionable content gaps
