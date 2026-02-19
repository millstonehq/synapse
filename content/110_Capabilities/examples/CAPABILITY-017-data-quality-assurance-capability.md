---
id: CAPABILITY-017
type: capability
title: Data Quality Assurance Capability
status: approved
owner: Head of Engineering
created: '2025-10-04T15:25:18.808Z'
updated: '2026-10-12T21:47:49.616Z'
tags:
  - capability
  - data-pipeline
summary: Data Quality Assurance Capability
evidence_links:
  - PROCESS-032
  - POLICY-027
  - PROCESS-066
example: true
---

## Domain

- Data Engineering
- Data Governance
- Analytics

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No data quality checks. Data consumers discover quality issues when reports show incorrect values or downstream services fail. No alerting or monitoring.
- **Level 1 - Ad hoc**: Some dbt tests exist for individual models but are not enforced consistently. Quality issues are reported by consumers via Slack.
- **Level 2 - Repeatable**: dbt tests run in CI for all mart-layer models. Quality check failures block production deployments. No runtime monitoring after data has landed.
- **Level 3 - Defined** (current): Automated Data Quality Validation Framework runs post-dbt on a schedule. Rules defined as YAML code in version control. CloudWatch metrics published per rule. P1 breaches trigger PagerDuty. Quality history tracked in DynamoDB for 90 days. Data Quality Dashboard available for self-service monitoring.
- **Level 4 - Managed**: Quality SLA defined per table and tracked as an SLO. Quality score trends reviewed in monthly stakeholder reports. Automated escalation paths for persistent P2 breaches.
- **Level 5 - Optimizing**: Quality rules auto-generated from dbt schema contracts. Anomaly detection on quality time series (statistical deviation alerts). Quality score improvement tracked as a quarterly OKR.

**Gap to Level 4**: Need to formalize per-table quality SLOs with defined target scores, implement escalation workflows for P2 rule breaches that persist beyond 48 hours, and introduce quality score trend reviews in the monthly data platform stakeholder meeting.

## Metrics

- P1 rule pass rate: Currently 98.4%, target > 99%
- P2/P3 rule pass rate: Currently 94.1%, target > 96%
- Mean time to detect quality issue: Currently 22 minutes (P1), target < 15 minutes
- Quality rule coverage (mart tables with at least one rule): Currently 87%, target 100%
- Quality history data availability (rules with 90-day history): Currently 100%
- Consumer-reported quality incidents per month: Currently 4, target < 2

## Evidence Links

- [[PROCESS-032|PROCESS-032]] - Data quality rule authoring and review process
- [[POLICY-027|POLICY-027]] - Data quality policy defining minimum rule coverage requirements for production tables
- [[PROCESS-066|PROCESS-066]] - Data pipeline capacity planning process (quality check Lambda capacity included)

## Notes

The organization advanced from Level 2 to Level 3 in Q2 2025 with the launch of the Data Quality Validation Framework and Data Quality Dashboard. Prior to this, quality was enforced only at build time (dbt CI tests) with no runtime monitoring.

Key improvements needed for Level 4:
- Define formal per-table quality SLOs with pass rate targets and document in the data catalog
- Implement automated Jira ticket creation for P2 breaches that remain unresolved after 48 hours
- Add quality score trends to monthly data platform stakeholder report (currently ad hoc)
