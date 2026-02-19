---
id: PRD-027
type: prd
title: Data Quality Dashboard PRD
status: approved
owner: Senior PM
created: '2025-03-28T17:24:58.044Z'
updated: '2025-03-15T08:23:03.749Z'
tags:
  - prd
  - data-pipeline
summary: Data Quality Dashboard PRD
related_tdds:
  - TDD-030
  - TDD-026
example: true
related_standards:
  - STANDARD-035
---

## Summary

Build a Data Quality Dashboard that gives data consumers, data engineers, and product stakeholders a single interface for monitoring data quality rule pass rates, investigating failures, viewing quality trend history, and tracking remediation. This replaces the current approach of checking CloudWatch dashboards and Slack alerts to understand data quality status. Technical design is driven by [[TDD-030|TDD-030: Data Lineage Tracker]] and [[TDD-026|TDD-026: Real-Time Event Processing Engine]], and must comply with [[STANDARD-035|STANDARD-035]].

## Goals

- Give data consumers a self-service view of data quality status without requiring Slack notifications or CloudWatch dashboard access
- Reduce mean time to detect (MTTD) data quality issues from 6 hours (current quality check schedule) to < 30 minutes for P1 rules
- Enable Data Engineering to track quality trend history and demonstrate SLA compliance to stakeholders
- Reduce quality-related support tickets to Data Engineering by 40% by enabling consumers to self-diagnose quality issues

## In Scope

- Per-table quality rule pass/fail status dashboard with last-run timestamp
- Rule-level detail view: observed value, threshold, trend history (30-day chart)
- Active breach list with severity, breach time, and link to rule definition
- Quality score summary per data domain (ingestion, staging, marts)
- Email digest for non-critical (P2/P3) rule breaches (daily rollup)

## Out of Scope

- Rule configuration UI (rules remain YAML-as-code in the data-pipeline repository)
- Remediation workflow management (tracked in Jira, not in the dashboard)
- Consumer-level quality subscriptions (v2)
- Mobile interface

## Users and Flows

**Data Analysts**: Check quality status of mart tables before building reports; investigate unexpected values by drilling into rule history; confirm quality restoration after a pipeline issue is resolved.

**Data Engineering On-Call**: Review active breaches on the main dashboard during incident response; correlate quality degradation with pipeline run history.

**Engineering Leadership**: View domain-level quality score trends for quarterly review; validate that quality SLAs are being met.

## Requirements

- Dashboard loads within 3 seconds for any user on corporate network
- Rule status reflects the most recent quality check run (within 30 minutes of check completion)
- Per-rule trend chart displays 30 days of observed values with pass/fail coloring
- Active breach list sortable by severity and breach duration
- Domain quality score calculated as: (passing P1 rules / total P1 rules) × 100
- Quality history queryable by table name and date range

## KPIs

- **MTTD improvement**: P1 quality breaches detected and surfaced in dashboard within 30 minutes (vs. current 6-hour average)
- **Self-service diagnosis rate**: 40% reduction in quality-related support tickets to Data Engineering within 90 days
- **Dashboard adoption**: > 70% of data consumer teams use the dashboard at least weekly within 3 months of launch
- **SLA reporting accuracy**: Domain quality scores match CloudWatch metrics within 0.1%

## Information Architecture

- Dashboard reads quality history from the DynamoDB `quality_results` table (written by the Data Quality Validation Framework)
- Active breach data served from real-time CloudWatch custom metric queries
- Table and domain metadata from the Data Lineage Tracker API

## Data Model

Core entities:

- **QualityRuleStatus**: Aggregated rule state. Fields: `rule_id`, `table`, `last_run_at`, `last_pass`, `current_value`, `threshold`, `severity`
- **QualityTrend**: Historical time series. Fields: `rule_id`, `evaluated_at`, `observed_value`, `pass`
- **DomainScore**: Aggregate. Fields: `domain`, `p1_pass_count`, `p1_total_count`, `score`, `as_of`

## Non-Functional

- Dashboard backed by read-only DynamoDB queries; no write access to quality data
- Authentication via internal SSO; no external access
- Dashboard data refreshes every 5 minutes via API polling; no real-time streaming required
- All quality data displayed with clear "as of" timestamps to avoid consumer confusion about data freshness

## Constraints

- Must read from the existing DynamoDB quality_results table; no new quality data stores
- Domain taxonomy must match the taxonomy used in quality rule YAML configurations
- No direct Trino or Iceberg queries from the dashboard backend (all data via quality API)

## Risks

- **Stale data confusion**: Users may interpret a 30-minute-old quality status as current. Mitigation: prominent "last updated" timestamp on all views; banner alert if quality data is > 1 hour old.
- **DomainScore calculation lag**: Domain scores depend on all P1 rules running successfully; a Lambda timeout could leave a rule stale. Mitigation: flag rules with no run in > 60 minutes as "stale" rather than "passing."

## Milestones

### M1: Core Dashboard (Week 1-3)

#### Deliverables

- Per-table rule status list with last-run timestamp and pass/fail indicator
- Active breach list sorted by severity
- Backend API reading from DynamoDB quality_results table

#### Acceptance Criteria

- Dashboard loads in < 3 seconds for tables with up to 500 quality rules
- Active breach list matches CloudWatch alert state within 1 refresh cycle (5 minutes)
- Authentication enforced via SSO

### M2: Trend History and Domain Scores (Week 4-6)

#### Deliverables

- 30-day trend chart per rule with pass/fail coloring
- Domain quality score summary view
- Stale rule flagging (no run in > 60 minutes)

#### Acceptance Criteria

- Trend chart renders with full 30-day history for all active rules
- Domain scores match manual calculation from DynamoDB query to within 0.1%
- Stale rules visually distinguished from passing rules

### M3: Alerts and Adoption (Week 7-8)

#### Deliverables

- Daily P2/P3 digest email for non-critical breaches
- Quality SLA report view for leadership (weekly rollup)
- Documentation and team onboarding sessions

#### Acceptance Criteria

- Digest email sent by 08:00 UTC daily with correct P2/P3 breach summary
- Leadership can view weekly domain score trend without analyst assistance
