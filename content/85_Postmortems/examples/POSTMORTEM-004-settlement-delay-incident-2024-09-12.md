---
id: POSTMORTEM-004
type: postmortem
title: Settlement Delay Incident 2024-09-12
status: approved
owner: On-Call Engineer
created: '2025-05-18T22:16:14.306Z'
updated: '2025-03-24T00:41:09.920Z'
tags:
  - postmortem
  - payment-processing
summary: Settlement Delay Incident 2024-09-12
incident_number: INC-75
severity: SEV-3
incident_date: '2026-03-27'
detection_time: '2025-11-03T10:18:28.761Z'
resolution_time: '2026-07-25T12:39:49.864Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-006
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On September 12, 2024, the nightly settlement batch job failed silently due to a misconfigured SQS dead-letter queue ARN. Approximately 4,200 captured transactions that should have been marked as `settled` remained in the `captured` state for approximately 18 hours. The delay affected daily reconciliation reports and caused incorrect balances to appear in the finance dashboard overnight. No payments were lost and all affected records were corrected by the following morning.

The incident was detected by automated alerting at 14:23 UTC and resolved at 15:47 UTC when the long-running query was identified and terminated. A subsequent pod restart cleared the exhausted connection pool.

## Timeline

- **02:05** - Nightly settlement batch job starts, processes Stripe settlement CSV for September 11.
- **02:07** - Settlement job encounters invalid SQS DLQ ARN in configuration. Job continues but silently discards failed state-change messages instead of queuing them.
- **02:30** - Settlement batch completes with exit code 0. No alert fires.
- **08:15** - Finance team opens the daily reconciliation dashboard and notices 4,200 transactions stuck in `captured` state.
- **08:22** - Finance escalates to Payments Engineering. On-call begins investigation.
- **08:40** - Engineer identifies the misconfigured DLQ ARN in the settlement job configuration. State-change events were silently dropped.
- **08:55** - Hotfix deployed with correct DLQ ARN. Re-run of settlement batch initiated.
- **10:18** - Settlement batch re-run completes. All 4,200 transactions updated to `settled` state.
- **10:30** - Reconciliation dashboard verified correct. Finance team notified. Incident closed.

## Impact

- **Duration**: ~8 hours of settlement delay (02:05 - 10:18 UTC)
- **Transactions affected**: 4,200 captured transactions remained in `captured` state overnight
- **Finance impact**: Overnight balance reports showed incorrect figures. No customer-facing impact.
- **Revenue impact**: No revenue lost; settlement delay only
- **SLA impact**: No availability breach. Internal settlement SLA (settled within 6 hours of capture) was breached.

## Root Cause Analysis

1. **Silent failure in settlement job due to misconfigured DLQ ARN**: The settlement batch job was configured with an incorrect SQS DLQ ARN introduced in a recent infrastructure migration. When state-change messages could not be published to SQS, the job silently discarded them and continued rather than failing with an error.

2. **No alerting on settlement job success/failure outcomes**: The settlement job produced an exit code 0 even when events were dropped. There was no metric or alert tracking the number of transactions successfully settled per batch run, so the silent failure went undetected until the finance team reviewed the dashboard 6 hours later.

## Resolution

1. Corrected the SQS DLQ ARN in the settlement job configuration
2. Redeployed the settlement job with the corrected configuration
3. Re-ran the settlement batch for September 11 to process all missed state transitions
4. Verified all 4,200 transactions were updated to `settled` state

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Fix settlement job to fail on SQS publish errors (non-zero exit code) | Payments team | P1 | 2024-09-14 | Completed |
| Add alert on settlement batch: transactions_settled_per_run < 1000 | SRE | P1 | 2024-09-18 | Completed |
| Add infrastructure migration checklist item for SQS ARN verification | Platform | P2 | 2024-09-30 | Completed |
| Add daily settlement completeness check to finance dashboard | Analytics | P3 | 2024-10-15 | Completed |

## Lessons Learned

- **What went well**: Finance team caught the issue at 08:15 from the dashboard. Re-run of the settlement batch was a clean recovery with no data loss.
- **What went poorly**: The settlement job silently discarded failures and exited with code 0. Silent failures in batch jobs are particularly dangerous because they can go undetected for hours.
- **What was lucky**: The misconfigured ARN affected only the DLQ routing, not the primary SQS queue. Had the primary queue ARN been wrong, the settlement job would have failed loudly.
