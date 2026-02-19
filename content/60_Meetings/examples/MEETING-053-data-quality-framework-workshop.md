---
id: MEETING-053
type: meeting
title: Data Quality Framework Workshop
status: approved
owner: Principal Engineer
created: '2024-04-09T09:55:35.287Z'
updated: '2026-01-01T19:40:40.542Z'
tags:
  - meeting
  - data-pipeline
summary: Data Quality Framework Workshop
company: DataPipeline
topic: Data Quality Framework Workshop
meeting_date: '2025-04-04T11:56:49.329Z'
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

- **Project**: Data Quality Initiative
- **Topic**: Data Quality Framework Workshop
- **Date/Time**: 2025-04-04 11:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Engineering Manager, QA Lead
- **Context**: Workshop to define a consistent data quality framework across all production pipelines, standardizing check types, thresholds, and incident response.

## Observations by Domain

- **Current State**: Data quality checks are inconsistently implemented — some pipelines use dbt tests, others use custom Python scripts, and some have no checks at all.
- **Check Coverage**: 47% of production datasets have at least one automated quality check; only 22% check all three minimum dimensions (completeness, uniqueness, schema).
- **Incident Trigger Mechanism**: Quality failures currently produce log entries in some pipelines and Slack alerts in others; no consistent PagerDuty routing.
- **Threshold Management**: Quality thresholds are hardcoded in pipeline code with no central management; changing a threshold requires a code deployment.
- **Consumer Awareness**: Downstream consumers are often unaware when data quality fails and continues to propagate; no flagging mechanism exists.
- **Tooling**: Team evaluated Great Expectations, dbt tests, and Soda Core; strong preference for dbt tests for batch and Great Expectations for raw ingestion validation.

## Key Metrics & Data Points

- **Dataset check coverage**: 47% have at least one check
- **Full minimum coverage (3 dimensions)**: 22% of datasets
- **Average time to detect quality incident**: 4.2 hours (too slow)
- **Average time to notify consumers**: 6.8 hours from incident start
- **Quality incidents last quarter**: 12 P2, 3 P1
- **False positive rate on existing checks**: 8% (thresholds too tight)

## Preliminary Scorecard Hooks

- Check Coverage: 2/5 - Well below target; majority of datasets unprotected
- Check Consistency: 2/5 - Multiple frameworks in use; no standard pattern
- Incident Response: 3/5 - Improving; routing still manual for some pipelines
- Consumer Communication: 2/5 - Slow and manual; no automated flagging
- Threshold Management: 2/5 - No centralized control; hardcoded values

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Bad data reaching consumers without detection | High | High | Principal Engineer | Mandate quality gates on all datasets serving consumers | 2025-05-01 |
| Framework fragmentation increases maintenance burden | Medium | High | Tech Lead | Standardize on dbt tests for batch; Great Expectations for raw | 2025-04-15 |
| Threshold tuning takes too long without central tooling | Medium | Medium | Data Platform Lead | Build threshold management config layer | 2025-06-01 |
| Slow consumer notification allows bad data to be acted on | High | Medium | Engineering Manager | Implement automated consumer notification on gate failure | 2025-05-15 |

## Decisions & Next Steps

### Decisions

- dbt schema tests are the standard for all batch pipeline quality checks; Great Expectations for raw ingestion
- All datasets serving external or cross-team consumers must have at minimum completeness, uniqueness, and schema checks before end of Q2
- Quality gate failures must route to PagerDuty via a standard alert configuration

### Action Items

- Draft Data Quality Framework standard document (Principal Engineer - 2025-04-18)
- Build dbt test templates for completeness, uniqueness, and referential integrity (Tech Lead - 2025-04-25)
- Implement PagerDuty routing for quality gate failures in the pipeline monitoring stack (Data Platform Lead - 2025-05-01)

### Follow-ups

- Review framework adoption progress at next monthly data platform review
- Schedule Q3 quality check coverage audit to track improvement
