---
id: POSTMORTEM-028
type: postmortem
title: Schema Registry Corruption 2025-02-08
status: approved
owner: Incident Commander
created: '2025-01-28T06:16:58.468Z'
updated: '2025-12-09T07:46:17.258Z'
tags:
  - postmortem
  - data-pipeline
summary: Schema Registry Corruption 2025-02-08
incident_number: INC-549
severity: SEV-1
incident_date: '2026-09-05'
detection_time: '2026-06-16T22:47:26.196Z'
resolution_time: '2024-09-17T15:12:55.849Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-054
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 8, 2025, the Schema Registry Service experienced a corruption event affecting 3 schema versions across 2 subjects. A Lambda function timeout during a high-volume schema registration burst left a DynamoDB item in a partially written state. Subsequent reads of the corrupted item caused deserialization failures for all producers and consumers referencing those schema versions, effectively blocking 3 Kafka topics for approximately 2 hours.

The incident was detected by automated `schema_deserialization_error_rate_high` alerts at 11:47 UTC. The corrupted schema versions were restored from a DynamoDB point-in-time recovery snapshot at 13:52 UTC.

## Timeline

- **11:30** - High-volume schema registration burst from 4 new upstream producers deploying simultaneously
- **11:34** - 3 Lambda executions time out at 29 seconds during DynamoDB write operations; partial item writes committed
- **11:42** - Downstream consumers begin receiving `SchemaDeserializationException` for affected schema IDs
- **11:47** - `schema_deserialization_error_rate_high` alert fires; on-call acknowledges
- **11:55** - On-call identifies all errors referencing the same 3 schema IDs
- **12:10** - Incident commander joins; decision made to restore from PITR snapshot rather than manual repair
- **12:25** - DynamoDB PITR restore initiated targeting 11:30 UTC snapshot
- **13:45** - PITR restore complete; schema versions verified as clean in restored table
- **13:52** - Traffic switched to restored table; Lambda cold starts complete; errors cease
- **14:10** - 30-minute stable observation window complete; incident closed

## Impact

- **Duration**: 2 hours 5 minutes (11:47 - 13:52 UTC)
- **Topics blocked**: 3 Kafka topics (order-events-v2, pricing-updates-v3, user-profile-changes-v2)
- **Producers blocked**: 4 new producers unable to publish; existing producers unaffected (using cached schemas)
- **Consumer impact**: Consumers on the 3 affected topics received deserialization errors for all new messages
- **SLA impact**: Schema Registry availability dropped to 98.6% for the day, breaching the 99.9% SLA
- **Data loss**: Zero — blocked producers retried successfully after schema restoration

## Root Cause Analysis

1. **Non-atomic DynamoDB writes**: The Lambda function wrote schema content as separate attribute updates in a multi-step operation rather than a single transactional write. A Lambda timeout between step 1 (write metadata) and step 2 (write schema content) left an item with metadata but no content — readable but corrupt.

2. **No write validation**: The schema registry did not validate item completeness after writes. Reads on the partially written item returned a valid JSON structure with an empty content field, which only failed at deserialization time — making detection slow and blast radius wide.

## Resolution

1. Identified the 3 corrupted schema IDs via error log analysis
2. Initiated DynamoDB PITR restore to a snapshot from before the corruption event
3. Verified restored schema versions against known-good copies in the producer repositories
4. Switched Lambda endpoint to the restored table

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Replace multi-step DynamoDB writes with `TransactWriteItems` | Data Engineering | P1 | 2025-02-12 | Completed |
| Add post-write validation step that reads back and verifies item completeness | Data Engineering | P1 | 2025-02-12 | Completed |
| Enable DynamoDB PITR backups with 24-hour retention on schema table | Infra | P1 | 2025-02-10 | Completed |
| Add `schema_version_corrupt` alert that detects empty content fields | SRE | P2 | 2025-02-20 | Completed |

## Lessons Learned

- **What went well**: PITR restore was faster than manual repair and resulted in verified-clean data. The alert fired within 5 minutes of corruption becoming visible to consumers.
- **What went poorly**: Non-atomic writes were a known risk pattern but had not been addressed as technical debt. The 2-hour recovery window was longer than necessary due to time spent evaluating manual repair before choosing PITR.
- **What was lucky**: PITR was already enabled on the DynamoDB table. If it had not been, manual repair would have been the only option.
