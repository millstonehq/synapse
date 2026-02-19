---
id: MEETING-054
type: meeting
title: Pipeline Performance Optimization Review
status: approved
owner: Product Manager
created: '2025-07-28T02:50:55.683Z'
updated: '2026-09-24T22:17:57.709Z'
tags:
  - meeting
  - data-pipeline
summary: Pipeline Performance Optimization Review
company: DataPipeline
topic: Pipeline Performance Optimization Review
meeting_date: '2024-04-15T13:42:22.612Z'
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

- **Project**: Data Platform Performance
- **Topic**: Pipeline Performance Optimization Review
- **Date/Time**: 2024-04-15 1:00 PM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Review of pipeline performance metrics following Q1 SLA miss incidents and identification of optimization opportunities.

## Observations by Domain

- **SLA Performance**: 6 of 38 pipelines missed their SLA window at least once in Q1; 3 pipelines missed SLA more than 5 times.
- **Spark Job Efficiency**: Average Spark executor utilization is 62%; data skew identified in 4 join-heavy models causing long-tail task durations.
- **Airflow Worker Saturation**: Peak hours (6-9 AM PT) show worker slot utilization reaching 95%; task queuing delays averaging 12 minutes during peaks.
- **dbt Model Runtimes**: Full refresh models averaging 45 minutes; 3 models identified as candidates for incremental conversion.
- **Data Volume Growth**: 3 pipelines saw >2x data volume growth in Q1 with no corresponding resource adjustment.
- **File Sizes**: 18 datasets have average file sizes below 10MB; small file problem causing excessive S3 list operations and slower reads.

## Key Metrics & Data Points

- **Pipelines missing SLA in Q1**: 6/38 (16%)
- **Average task queue delay at peak**: 12 minutes
- **Spark executor utilization**: 62% average
- **Datasets with small file problem (<10MB avg)**: 18
- **Full-refresh models taking >30 minutes**: 3
- **Data volume growth pipelines (>2x)**: 3

## Preliminary Scorecard Hooks

- SLA Adherence: 3/5 - 84% compliance is below 95% target; concentrated in few pipelines
- Resource Utilization: 3/5 - Low executor utilization masks skew problems
- Airflow Capacity: 3/5 - Worker saturation at peak hours is a bottleneck
- Data Layout: 2/5 - Small file problem widespread; compaction needed
- Model Efficiency: 3/5 - 3 models need incremental migration

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Peak-hour worker saturation causes cascading SLA misses | High | High | Data Platform Lead | Add Airflow worker autoscaling; stagger pipeline start times | 2024-05-01 |
| Data volume growth pipelines will miss SLA without scaling | High | Medium | Tech Lead | Review and increase resource allocations for affected pipelines | 2024-04-30 |
| Small file problem degrades read performance over time | Medium | Certain | Principal Engineer | Run compaction jobs; enforce min file size in write configs | 2024-05-15 |
| Spark data skew causes unpredictable job durations | Medium | High | Tech Lead | Enable AQE skew join optimization for identified models | 2024-04-25 |

## Decisions & Next Steps

### Decisions

- Airflow worker autoscaling will be implemented before end of April to address peak-hour saturation
- All Spark jobs must have Adaptive Query Execution (AQE) enabled; this becomes a pipeline code standard
- Compaction jobs will be scheduled weekly for all datasets with average file sizes below 50MB

### Action Items

- Implement Airflow worker autoscaling configuration (Data Platform Lead - 2024-05-01)
- Enable AQE on the 4 identified skew-prone models (Tech Lead - 2024-04-25)
- Schedule weekly compaction jobs for 18 small-file datasets (Principal Engineer - 2024-05-15)

### Follow-ups

- Monthly SLA adherence review to track improvement
- Q2 performance review in July to assess impact of optimizations
