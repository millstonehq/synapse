---
id: REPORT-044
type: report
title: Data Platform Q1 2025 Health Report
status: review
owner: Data Tech Lead
created: '2024-03-04T17:43:04.234Z'
updated: '2025-05-15T18:45:05.208Z'
tags:
  - report
  - data-pipeline
summary: Data Platform Q1 2025 Health Report
company: DataPipeline
report_month: 2025-03
report_type: company
overall_health: poor
confidence: low
active_initiatives_count: 2
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Q1 Actual | Status |
|--------|--------|-----------|--------|
| Pipeline availability | 99.9% | 99.57% | Below target |
| Ingestion lag P95 (monthly avg) | < 15 min | 15.3 min | Below target |
| Transformation success rate | > 98% | 98.0% | On target |
| Quality check pass rate | > 99.5% | 99.4% | Below target |
| SEV-1 incidents | 0 | 2 | Below target |

Q1 2025 was a challenging quarter for the data platform. Two SEV-1 incidents (Kafka outage in January, Schema Registry corruption in February) drove availability below the quarterly target. March recovery was strong, and the platform exited Q1 on a stable trajectory.

## Key Highlights

- **Q1 incident summary**: 2 SEV-1, 1 SEV-2, 2 SEV-3 incidents. Both SEV-1 incidents had associated postmortems with action items in progress. The Kafka outage was the highest-impact event, causing 36 hours of elevated lag.
- **Streaming ingestion milestone**: 17 of 22 topics migrated from batch to streaming ingestion. Average data freshness lag for covered topics reduced from 6 hours to 13 minutes.
- **Iceberg adoption**: 100% of new analytical tables created in Q1 use Iceberg format. Legacy tables on Parquet/Hive: 34 remaining, targeted for migration in Q2 and Q3.

## Active Initiatives

1. **IAM permission audit**: In progress following March 20 incident; 12 of 23 service accounts reviewed.
2. **Remaining tier-2 streaming migration**: 5 topics still on batch; target completion Q2 week 3.
3. **Schema registry reliability hardening**: Transactional write protection deployed; monitoring for 30 days before closing action item.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Jan 12 | SEV-2 | 4 hours | Kafka broker leadership election storm |
| Feb 8 | SEV-1 | 2 hours | Schema Registry DynamoDB partial write corruption |
| Mar 14 | SEV-3 | 45 min | Schema mismatch from new upstream producer |
| Mar 20 | SEV-2 | 15 min | IAM permission escalation in data lake |

## Risks

- **Critical**: IAM permission audit incomplete; over-privileged service accounts remain a risk until audit closes (target April 15).
- **Medium**: 34 legacy Hive/Parquet tables still require Iceberg migration; until migrated, these tables do not support time travel or schema evolution.

## Next Month Focus

- Complete IAM permission audit and remediation
- Migrate final 5 streaming topics
- Begin Q2 planning for legacy table Iceberg migration backlog
