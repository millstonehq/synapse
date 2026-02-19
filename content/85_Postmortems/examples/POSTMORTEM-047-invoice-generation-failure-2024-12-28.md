---
id: POSTMORTEM-047
type: postmortem
title: Invoice Generation Failure 2024-12-28
status: approved
owner: On-Call Engineer
created: '2025-06-21T04:45:47.011Z'
updated: '2026-03-29T11:44:19.695Z'
tags:
  - postmortem
  - billing-engine
summary: Invoice Generation Failure 2024-12-28
incident_number: INC-928
severity: SEV-4
incident_date: '2025-12-25'
detection_time: '2025-09-06T16:11:56.675Z'
resolution_time: '2024-11-24T09:07:53.972Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-095
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On December 28, 2024, the Invoice Generation Pipeline failed to process end-of-month invoices for approximately 3,800 customers. The failure was caused by a memory exhaustion condition in the invoice generation workers triggered by an unusually large tax calculation batch response from Avalara. The pipeline stalled for approximately 4 hours before the on-call engineer identified the root cause and restarted affected workers. All invoices were successfully generated after recovery.

The incident was detected by a monitoring alert at 02:14 UTC. It was resolved at 06:22 UTC. All affected customers received their invoices by 08:00 UTC, within the 24-hour delivery SLA.

## Timeline

- **00:00** - Month-end invoice generation pipeline triggered for December 2024 billing period
- **01:45** - Pipeline completes first 30,000 invoices normally
- **02:12** - Invoice generation workers begin logging OOM warnings as a large-enterprise batch with complex usage is processed
- **02:14** - `invoice_pipeline_worker_oom` alert fires. On-call engineer acknowledges.
- **02:20** - On-call checks for recent deploys — none in the last 48 hours. Rules out deploy-related cause.
- **02:35** - On-call restarts workers. Workers restart successfully but fail again within 5 minutes on the same batch.
- **02:42** - On-call escalates to Billing tech lead per runbook escalation timeline.
- **03:00** - Tech lead identifies that a single customer's tax calculation request returned a 48MB response from Avalara (normal: < 500KB), caused by a misconfigured tax code that duplicated line items.
- **03:15** - Problematic customer batch is isolated and skipped to allow the remaining pipeline to complete.
- **04:30** - Remaining 3,800 invoices generated for all other customers. Avalara misconfiguration root cause confirmed.
- **06:22** - Isolated customer batch processed successfully after applying a chunking workaround. Incident closed.

## Impact

- **Duration**: ~4 hours (02:14 - 06:22 UTC)
- **Customers affected**: ~3,800 customers whose invoices were delayed. Invoice delivery remained within 24-hour SLA.
- **Revenue impact**: Estimated $12,000 in delayed payment processing (no permanent revenue loss — charges collected after invoice delivery)
- **SLA impact**: Invoice generation SLA met (< 24-hour delivery). Pipeline availability SLA missed.
- **Customer communications**: No customer-facing status page update required as invoices were delivered within SLA.

## Root Cause Analysis

1. **Misconfigured customer tax code caused response explosion**: A tax code misconfiguration for one enterprise customer caused Avalara to return a response with 47,000 duplicate line items (expected: ~50) when tax was calculated for their large December usage batch. The response was 48MB vs. the typical < 500KB.

2. **No response size guard in the Tax Calculation Engine adapter**: The Avalara adapter had no maximum response size limit. The 48MB response was loaded entirely into memory before the pipeline could detect and handle the anomaly, causing worker OOM.

The tax code misconfiguration was a configuration error created during onboarding that had not been exercised at scale until the December invoice included the full year of usage. The combination of a large batch and a multiplied response size overwhelmed worker memory limits.

## Resolution

1. Isolated the problematic customer batch and skipped it to unblock the remaining pipeline
2. Processed the isolated batch with a chunking workaround that split the tax calculation into smaller requests
3. Corrected the customer's Avalara tax code configuration

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add 5MB maximum response size guard in Avalara adapter | Billing Engineering | P1 | 2025-01-10 | Completed |
| Add pre-invoice tax calculation dry-run check for large accounts | Billing Engineering | P1 | 2025-01-15 | In progress |
| Validate all enterprise customer Avalara tax code configurations | Finance / Billing Ops | P1 | 2025-01-20 | In progress |
| Add `invoice_pipeline_worker_oom` alert with memory trend pre-alert | SRE | P2 | 2025-01-20 | Pending |
| Update runbook with large-account isolation and chunking procedure | On-call | P2 | 2025-01-20 | Pending |

## Lessons Learned

- **What went well**: Alerting fired promptly. On-call followed runbook escalation timeline. Tech lead identified root cause within 18 minutes of joining. All invoices delivered within SLA despite the failure.
- **What went poorly**: No size guard on the Avalara response allowed a single misconfigured customer to OOM multiple workers. The runbook had no procedure for isolating a problematic batch, delaying recovery.
- **What was lucky**: The incident occurred at 02:00 UTC on December 28, leaving sufficient time to recover and still meet the invoice delivery SLA before customers' business day began.
- **Process improvement**: Add a pre-invoice tax dry-run validation step for enterprise accounts with large usage batches before the month-end pipeline runs.
