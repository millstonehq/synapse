---
id: POSTMORTEM-027
type: postmortem
title: Data Pipeline Data Loss 2024-11-18
status: review
owner: On-Call Engineer
created: '2024-11-17T04:34:33.477Z'
updated: '2025-09-21T11:20:48.850Z'
tags:
  - postmortem
  - data-pipeline
summary: Data Pipeline Data Loss 2024-11-18
incident_number: INC-548
severity: SEV-1
incident_date: '2026-11-04'
detection_time: '2026-01-03T23:47:07.316Z'
resolution_time: '2024-05-26T09:53:20.542Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-056
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 18, 2024, the data pipeline experienced a data loss event affecting approximately 340,000 records from 3 source topics over a 2-hour window (02:00–04:00 UTC). A bug in the Data Lake Ingestion Service's checkpoint recovery logic caused the service to replay from an incorrect Kafka offset after an ECS task crash, skipping forward past the gap rather than replaying it.

The issue was not detected in real time. The Data Quality Monitor's completeness checks identified gaps in the orders, inventory, and session event Iceberg tables at 10:15 UTC — 6 hours after the loss window. All 340,000 missing records were recovered from Kafka's 7-day retention window by 18:30 UTC via a manual replay job.

## Timeline

- **02:00** - ECS ingestion task crashes during high-volume window; automatic ECS restart triggered
- **02:03** - Task restarts and reads checkpoint offset from Aurora PostgreSQL
- **02:04** - Checkpoint recovery bug causes task to read offset written *after* the crash; consumer skips to 04:00 UTC, losing 2 hours of events
- **04:00** - Ingestion resumes at correct real-time position; no further data loss
- **10:15** - Data Quality Monitor completeness rules fire for orders, inventory, session tables
- **10:22** - On-call engineer acknowledges quality alerts
- **11:00** - Root cause identified: checkpoint offset written before Iceberg commit confirmation
- **12:30** - Manual Kafka replay job started for affected topics covering 02:00–04:00 UTC
- **18:30** - Replay complete; all 340,000 missing records backfilled
- **19:00** - Downstream Iceberg tables reprocessed; analytics consumers confirmed current

## Impact

- **Records lost (before recovery)**: ~340,000 across orders, inventory, and session event topics
- **Recovery time**: 16.5 hours from incident start to full data restoration
- **Analytics impact**: Tier-1 dashboards showed gaps for 8+ hours before recovery
- **Permanent data loss**: Zero — all records recovered from Kafka retention
- **SLA impact**: Data freshness SLA breached for 3 topics during recovery window

## Root Cause Analysis

1. **Checkpoint write timing bug**: The ingestion service wrote Aurora checkpoint offsets *before* confirming the Iceberg write commit succeeded. A task crash after the offset write but before the Iceberg commit left the checkpoint pointing to a future offset. On restart, the service resumed from that future offset, silently skipping the uncommitted window.

2. **No gap detection alerting**: No real-time alert existed for Kafka offset continuity gaps. Detection relied entirely on quality completeness checks running on a 6-hour delay, making the detection window unacceptably long for a data loss event.

## Resolution

1. Identified the 2-hour offset gap by comparing Aurora checkpoint values against Iceberg table watermarks
2. Launched a manual Kafka replay consumer targeting offset range 02:00–04:00 UTC on all 3 affected topics
3. Backfilled 340,000 missing records into the affected Iceberg tables
4. Re-triggered downstream dbt transformation models to reprocess the corrected source data

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Fix checkpoint write to occur only after successful Iceberg commit | Data Engineering | P1 | 2024-11-22 | Completed |
| Add Kafka offset continuity alert (gap > 1,000 offsets triggers page) | SRE | P1 | 2024-11-25 | Completed |
| Add crash-recovery integration test covering checkpoint ordering | Data Engineering | P2 | 2024-12-06 | Completed |
| Reduce quality completeness check frequency from 6 hours to 30 minutes | Data Engineering | P2 | 2024-12-15 | Completed |

## Lessons Learned

- **What went well**: 7-day Kafka retention made full recovery possible. No permanent data loss occurred once the gap was identified.
- **What went poorly**: 6-hour detection gap is unacceptable for a data loss event. Real-time offset gap monitoring should have been in place from day one.
- **What was lucky**: The incident was within the 7-day Kafka retention window. Discovery even one week later would have meant permanent, unrecoverable data loss.
