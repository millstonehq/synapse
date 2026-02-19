---
id: MEETING-058
type: meeting
title: Data Governance Alignment Meeting
status: approved
owner: Principal Engineer
created: '2024-01-03T15:32:12.073Z'
updated: '2026-06-16T23:04:55.156Z'
tags:
  - meeting
  - data-pipeline
summary: Data Governance Alignment Meeting
company: DataPipeline
topic: Data Governance Alignment Meeting
meeting_date: '2025-05-23T00:33:27.599Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Data Governance Program
- **Topic**: Data Governance Alignment Meeting
- **Date/Time**: 2025-05-23 9:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Alignment session between engineering and Data Governance on catalog coverage, PII classification progress, and retention policy enforcement ahead of the annual compliance audit.

## Observations by Domain

- **Catalog Coverage**: 71% of curated datasets have complete catalog entries; 29% are missing owner, classification, or lineage. Audit requires 100% coverage for all datasets serving external customers.
- **PII Classification**: 14 datasets confirmed to contain PII; 8 have been formally classified and approved; 6 are pending governance review.
- **Retention Policy Enforcement**: Automated lifecycle policies are in place for 60% of raw zone buckets; 40% still require manual enforcement.
- **Lineage Tracking**: Data lineage is recorded for dbt models via dbt docs; Kafka-sourced data lineage is partially documented but not automated.
- **Access Reviews**: Quarterly access reviews are required; last review was completed 5 months ago — overdue.
- **GDPR Deletion Compliance**: 2 open deletion requests are pending; current process is manual and requires 5 business days average, which is at risk of breaching the 30-day GDPR obligation.

## Key Metrics & Data Points

- **Catalog completeness**: 71% (target: 100% for audit)
- **Datasets with PII pending classification**: 6
- **Retention lifecycle automation coverage**: 60%
- **Months since last access review**: 5 (target: quarterly)
- **Open GDPR deletion requests**: 2 (average resolution: 5 business days)
- **Days until compliance audit**: 45

## Preliminary Scorecard Hooks

- Catalog Coverage: 3/5 - Below audit target; 45 days to close gap
- PII Classification: 3/5 - Progress made; 6 datasets still pending
- Retention Automation: 3/5 - Majority covered; raw zone gaps need closing
- Access Review Timeliness: 2/5 - Overdue by 2 months; must be completed before audit
- GDPR Compliance: 3/5 - Process in place but manual; automation needed

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Catalog gaps fail compliance audit | High | High | Data Platform Lead | Sprint to complete catalog entries for all external-facing datasets | 2025-06-15 |
| 6 unclassified PII datasets create audit exposure | High | High | Engineering Manager | Complete PII classification reviews for 6 pending datasets | 2025-06-01 |
| Overdue access review is a compliance violation | High | Certain | Principal Engineer | Complete access review within 2 weeks | 2025-06-06 |
| GDPR deletion process too slow for volume growth | Medium | High | Tech Lead | Automate deletion workflow; target 24-hour resolution | 2025-07-01 |

## Decisions & Next Steps

### Decisions

- Catalog completion for all external-facing datasets is a P1 priority before the compliance audit on July 7
- Access review must be completed by June 6; Principal Engineer is the accountable owner
- GDPR deletion automation will be scoped as a sprint story for Q3

### Action Items

- Complete catalog entries for all external-facing datasets (Data Platform Lead - 2025-06-15)
- Complete PII classification reviews for 6 pending datasets (Engineering Manager - 2025-06-01)
- Complete overdue access review (Principal Engineer - 2025-06-06)

### Follow-ups

- Pre-audit readiness review scheduled for June 25
- Automation scoping for GDPR deletion workflow to be added to Q3 roadmap
