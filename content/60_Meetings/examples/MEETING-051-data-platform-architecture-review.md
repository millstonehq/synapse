---
id: MEETING-051
type: meeting
title: Data Platform Architecture Review
status: approved
owner: Engineering Manager
created: '2025-04-04T21:02:07.859Z'
updated: '2025-06-07T04:00:41.619Z'
tags:
  - meeting
  - data-pipeline
summary: Data Platform Architecture Review
company: DataPipeline
topic: Data Platform Architecture Review
meeting_date: '2024-04-05T04:23:05.045Z'
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

- **Project**: Data Platform Modernization
- **Topic**: Data Platform Architecture Review
- **Date/Time**: 2024-04-05 10:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Platform Lead
- **Attendees (product)**: Engineering Manager, QA Lead
- **Context**: Quarterly review of data platform architecture health covering ingestion, transformation, and serving layers.

## Observations by Domain

- **Ingestion Layer**: Kafka-based ingestion is stable; 14 active topics with schema registry coverage at 100% for new topics. Legacy CSV-over-SFTP ingestion still active for 3 sources — migration to Kafka planned.
- **Transformation**: dbt models covering 62 curated datasets; coverage of critical revenue models is strong. Three models still use deprecated full-refresh strategy — should migrate to incremental.
- **Orchestration**: Airflow 2.6 running on Kubernetes; scheduler uptime 99.4% last quarter. 8 DAGs have no alerting configured — gap identified.
- **Data Quality**: 47 quality gates deployed; 6 datasets have no quality checks. Data quality incident rate down 30% quarter-over-quarter.
- **Catalog Coverage**: 71% of curated datasets have complete catalog entries; remaining 29% missing owner or PII classification.
- **Monitoring**: Grafana dashboards cover all critical pipelines. Consumer lag alerting is in place for all production consumer groups.

## Key Metrics & Data Points

- **Active pipelines**: 38 batch DAGs, 12 streaming consumer groups
- **Data quality incident rate**: 2.1 incidents/week (down from 3.0 previous quarter)
- **Schema registry coverage**: 100% for new topics; 14/22 legacy topics migrated
- **Catalog completeness**: 71% of curated datasets with full metadata
- **Airflow scheduler uptime**: 99.4% last 90 days
- **Average pipeline latency vs SLA**: 94% of SLA-bound pipelines meeting targets

## Preliminary Scorecard Hooks

- Ingestion: 4/5 - Kafka-first strategy mature; 3 legacy sources remaining
- Transformation: 4/5 - dbt coverage strong; 3 full-refresh models need migration
- Orchestration: 4/5 - Stable with high uptime; alerting gaps on 8 DAGs
- Data Quality: 3/5 - Improving trend; 6 datasets still unprotected
- Catalog and Governance: 3/5 - 71% completeness; ownership gaps need resolution

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| 6 datasets with no quality gates allow silent corruption | High | Medium | Data Platform Lead | Add baseline quality gates to all unprotected datasets | 2024-05-01 |
| 3 legacy SFTP sources create reliability dependency | Medium | High | Tech Lead | Migrate 2 sources to Kafka connectors this quarter | 2024-06-30 |
| 8 DAGs without alerting create blind spots | Medium | High | Principal Engineer | Configure alerting for all DAGs via standard runbook | 2024-04-20 |
| Catalog ownership gaps block access decisions | Low | Medium | Engineering Manager | Assign owners to all uncatalogued datasets | 2024-05-15 |

## Decisions & Next Steps

### Decisions

- Kafka-first ingestion is the approved strategy; no new SFTP ingestion connectors will be created
- All new datasets must have quality gates and catalog entries before promotion to production (enforced via onboarding checklist)
- Airflow alerting must be configured for all DAGs by end of April

### Action Items

- Add quality gates to 6 unprotected datasets (Data Platform Lead - 2024-05-01)
- Configure alerting for 8 DAGs without coverage (Principal Engineer - 2024-04-20)
- Begin migration plan for 3 remaining legacy SFTP sources (Tech Lead - 2024-04-15)

### Follow-ups

- Monthly data quality review with team leads
- Revisit schema registry migration progress for legacy topics next quarter
