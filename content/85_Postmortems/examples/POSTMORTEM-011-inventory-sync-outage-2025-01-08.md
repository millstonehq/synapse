---
id: POSTMORTEM-011
type: postmortem
title: Inventory Sync Outage 2025-01-08
status: proposed
owner: Incident Commander
created: '2024-01-31T02:42:58.934Z'
updated: '2025-06-04T12:52:38.819Z'
tags:
  - postmortem
  - inventory-management
summary: Inventory Sync Outage 2025-01-08
incident_number: INC-262
severity: SEV-4
incident_date: '2024-01-30'
detection_time: '2025-09-24T18:51:40.667Z'
resolution_time: '2026-04-20T11:36:31.785Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-026
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 8, 2025, the Warehouse Sync Gateway experienced a 62-minute outage that halted all inbound stock event processing. The root cause was a DynamoDB idempotency cleanup Lambda function that ran without concurrency limits and consumed the table's full provisioned write capacity, starving the sync adapters of the write throughput needed to record processed event IDs. All 12 warehouse connections queued up and timed out.

The incident was detected by automated alerting at 09:14 UTC when warehouse sync DLQ depth exceeded the alert threshold. Resolution required temporarily disabling the cleanup job and manually reprocessing the backlog of 847 queued webhook deliveries. No stock data was permanently lost, but a temporary freeze in stock level updates affected downstream services for the duration of the outage.

## Timeline

- **09:02** - Idempotency store cleanup Lambda function starts scheduled run (weekly cadence)
- **09:05** - DynamoDB provisioned write capacity fully consumed by cleanup job; sync adapters begin failing to record idempotency keys
- **09:07** - Warehouse webhook deliveries begin failing with 500 errors; WMS providers begin retrying
- **09:12** - DLQ depth exceeds 100 messages; `inventory_sync_dlq_high` alert fires
- **09:14** - On-call engineer acknowledges alert and begins investigation
- **09:18** - On-call checks recent deploys — none since Jan 6. Begins reviewing CloudWatch metrics.
- **09:25** - DynamoDB write throttle errors identified in CloudWatch; cleanup Lambda identified as consumer
- **09:28** - On-call disables the cleanup Lambda function to halt write capacity consumption
- **09:35** - DynamoDB write capacity recovers; sync adapters resume processing
- **09:42** - Backlog processing begins; DLQ messages being reprocessed successfully
- **10:12** - DLQ fully drained; all 847 backlogged events processed and stock levels updated
- **10:16** - Incident formally closed after 15-minute stable monitoring window

## Impact

- **Duration**: 62 minutes of full sync outage (09:07 - 10:09 UTC for last warehouse reconnect)
- **Warehouses affected**: All 12 active warehouse connections
- **Events backlogged**: 847 stock movement events queued during the outage
- **Stock level lag**: Stock levels were stale for up to 62 minutes; no orders were blocked as the order service uses a 5-minute staleness tolerance
- **Revenue impact**: No direct revenue impact; stock reservation decisions during the window used slightly stale data
- **Downstream services**: Real-time stock dashboard showed stale data during the outage window

## Root Cause Analysis

1. **No concurrency limit on cleanup Lambda**: The idempotency store cleanup function was configured with the default Lambda concurrency limit (unbounded). When it started scanning and deleting expired records, it generated burst write traffic that immediately consumed all provisioned DynamoDB write capacity. There was no mechanism to throttle or time-limit the cleanup operation.

2. **Under-provisioned DynamoDB write capacity**: The idempotency table was provisioned for the steady-state write pattern of sync adapter operations. It had no headroom for concurrent administrative operations like bulk cleanup, making it vulnerable to any write-heavy background job.

## Resolution

1. Disabled the idempotency cleanup Lambda to restore DynamoDB write capacity
2. Monitored DLQ drain to confirm all backlogged events were processed correctly
3. Verified stock level accuracy against warehouse-reported counts after full recovery
4. Scheduled a revised cleanup approach (batched deletes with rate limiting) for the following week

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add concurrency limit (max 1) and rate-limited batch deletes to cleanup Lambda | Inventory Engineering | P1 | 2025-01-15 | Completed |
| Switch DynamoDB idempotency table to on-demand capacity to handle burst operations | Inventory Engineering | P1 | 2025-01-15 | Completed |
| Add `inventory_sync_dynamodb_throttle` alert for write throttle events | SRE | P2 | 2025-01-22 | Completed |
| Add cleanup job impact assessment to runbook pre-run checklist | On-call | P2 | 2025-01-22 | Pending |

## Lessons Learned

- **What went well**: Automated alerting caught the incident quickly (5-minute detection). DLQ backlog was fully recoverable with no data loss.
- **What went poorly**: The cleanup Lambda had no write rate limiting, and DynamoDB capacity was not sized to absorb concurrent administrative operations. These were known risks that had not been addressed.
- **What was lucky**: The order service's staleness tolerance prevented any order fulfillment decisions from being blocked during the outage window.
