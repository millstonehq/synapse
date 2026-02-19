---
id: MEETING-059
type: meeting
title: Airflow to Dagster Migration Review
status: approved
owner: Product Manager
created: '2024-10-11T20:11:15.273Z'
updated: '2025-07-23T09:45:24.273Z'
tags:
  - meeting
  - data-pipeline
summary: Airflow to Dagster Migration Review
company: DataPipeline
topic: Airflow to Dagster Migration Review
meeting_date: '2026-06-11T09:52:33.535Z'
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

- **Project**: Orchestration Platform Migration
- **Topic**: Airflow to Dagster Migration Review
- **Date/Time**: 2026-06-11 9:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Mid-point review of the Airflow to Dagster migration project; 18 of 38 DAGs migrated so far. Assessing progress, blockers, and decision on scope for remaining migration.

## Observations by Domain

- **Migration Progress**: 18 of 38 DAGs fully migrated to Dagster jobs; 12 more in progress; 8 not yet started.
- **Developer Experience**: Engineers report significantly better software-development-style testing with Dagster; unit testable ops are a major improvement over Airflow's testing story.
- **Operational Stability**: Dagster-migrated pipelines have had 0 scheduler-related incidents in 8 weeks vs. 2 Airflow scheduler incidents in the same period.
- **Migration Effort**: Average migration effort is 2-3 days per DAG for simple pipelines; complex DAGs with many sensors or cross-DAG dependencies are taking 5-7 days.
- **Dual-operation Cost**: Running both Airflow and Dagster in parallel is adding ~$800/month in compute; accelerating the migration reduces this overhead.
- **Feature Gap**: Airflow's ExternalTaskSensor has no direct equivalent in Dagster; the team has built a custom asset dependency pattern but it adds 1 day per affected pipeline.

## Key Metrics & Data Points

- **DAGs migrated**: 18/38 (47%)
- **DAGs in progress**: 12
- **Average migration effort (simple)**: 2-3 days
- **Average migration effort (complex)**: 5-7 days
- **Dagster scheduler incidents (8 weeks)**: 0
- **Airflow scheduler incidents (8 weeks)**: 2
- **Dual-operation monthly cost overhead**: ~$800

## Preliminary Scorecard Hooks

- Migration Velocity: 3/5 - On track for complex DAGs; simple DAGs could move faster
- Stability Improvement: 5/5 - Dagster pipelines showing materially better uptime
- Developer Experience: 4/5 - Team satisfaction with Dagster significantly higher
- Cost Management: 3/5 - Dual-operation overhead is contained but growing with time
- Feature Parity: 4/5 - Custom sensor pattern works; minor friction on complex cases

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Dual-operation overhead grows if migration drags | Medium | High | Data Platform Lead | Accelerate migration of remaining simple DAGs to close Airflow quickly | 2026-07-15 |
| Complex DAGs with sensor dependencies are underestimated | Medium | High | Tech Lead | Re-estimate all remaining complex DAGs; adjust timeline | 2026-06-18 |
| Airflow scheduled for decommission before all DAGs migrated | High | Medium | Principal Engineer | Confirm Airflow decommission date and map it to migration completion | 2026-06-18 |

## Decisions & Next Steps

### Decisions

- Migration will continue; Airflow decommission target date is September 1, 2026
- Simple DAGs (no sensors, no cross-DAG deps) will be batch-migrated in a dedicated sprint to close Airflow faster
- The custom asset dependency pattern for ExternalTaskSensor replacement is adopted as the standard; add to migration guide

### Action Items

- Re-estimate all remaining 8 un-started DAGs with complexity classification (Tech Lead - 2026-06-18)
- Plan a dedicated simple-DAG batch migration sprint for July (Data Platform Lead - 2026-06-18)
- Update the Airflow-to-Dagster migration guide with the custom sensor pattern (Principal Engineer - 2026-06-25)

### Follow-ups

- Bi-weekly migration progress check through September
- Airflow decommission readiness review scheduled for August 15
