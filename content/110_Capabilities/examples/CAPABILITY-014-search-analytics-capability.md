---
id: CAPABILITY-014
type: capability
title: Search Analytics Capability
status: deprecated
owner: Head of Engineering
created: '2025-11-11T20:34:44.342Z'
updated: '2026-09-26T17:10:05.196Z'
tags:
  - capability
  - search-platform
summary: Search Analytics Capability
evidence_links:
  - POLICY-022
  - POLICY-021
  - PROCESS-029
example: true
---

## Domain

- Search Platform
- Data Analytics
- Product Intelligence

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No search analytics. Teams have no visibility into what users are searching for, which queries return zero results, or whether search quality is improving or degrading.
- **Level 1 - Ad hoc**: Engineers run manual SQL queries against the search logs database on request. Insights are shared informally via Slack or spreadsheets. No consistent metrics definitions.
- **Level 2 - Repeatable**: A basic Kibana dashboard exists with query volume and top terms. Metrics are computed nightly. Product managers must ask engineering to pull custom reports.
- **Level 3 - Defined** (current): Self-serve analytics dashboard is operational. Metrics (CTR, zero-result rate, NDCG@10, MRR) are formally defined and tracked weekly. Data is refreshed every 15 minutes. CSV export is available. The analytics pipeline is documented, monitored, and has an SLO.
- **Level 4 - Managed**: Real-time anomaly detection alerts on zero-result rate spikes and CTR drops. Cohort analysis enabled (e.g., CTR by user segment, by content category). A/B experiment result tracking integrated into the same dashboard.
- **Level 5 - Optimizing**: Analytics signals feed directly into the ranking model retraining pipeline. Dashboard usage and insight quality are tracked to optimize the analytics product itself. Proactive content gap recommendations generated from zero-result trends.

**Gap to Level 4**: Requires real-time anomaly detection on the analytics metrics (currently only batch-computed), and A/B experiment tracking integration. The analytics pipeline currently operates on a 15-minute aggregation cycle, which needs to be supplemented with a streaming anomaly detection layer.

## Metrics

- Dashboard data freshness: Currently 12 minutes average, target < 15 minutes
- Unique dashboard active users per week: Currently 18, target > 20
- Time-to-insight for zero-result analysis: Currently 8 minutes median, target < 15 minutes
- Analytics pipeline availability: Currently 99.8%, target > 99.5% (exceeding target)
- Events captured per day: ~4.2 million search and click events
- Query history retention: 90 days hot (OpenSearch), 1 year cold (S3 + Glacier)

## Evidence Links

- [[POLICY-022|Search Analytics Data Policy]] - Defines permitted uses of search behavioral data and PII restrictions
- [[POLICY-021|Search Data Governance Policy]] - Mandates aggregate-only storage (no raw user-event history beyond 90 days)
- [[PROCESS-029|Analytics Data Review Process]] - Quarterly review of analytics data collection scope and retention compliance

## Notes

This capability is marked deprecated because it is being superseded by a unified observability platform that will consolidate search analytics, infrastructure metrics, and business KPIs into a single tool. The current search analytics dashboard (Kibana-based) will be migrated to the new platform in Q1 2027.

Until migration is complete, the current capability remains operational and is the authoritative source for search quality metrics. Teams should continue using the existing dashboard for day-to-day search quality monitoring. New feature development against the current Kibana dashboard has been paused.

Key risks during deprecation period:
- Metrics continuity must be preserved across the migration — no gaps in NDCG@10 or CTR trend data
- The new platform must replicate the CSV export and date-range filtering functionality that content operators depend on
