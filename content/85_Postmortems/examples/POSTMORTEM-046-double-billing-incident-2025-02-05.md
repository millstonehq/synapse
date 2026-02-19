---
id: POSTMORTEM-046
type: postmortem
title: Double Billing Incident 2025-02-05
status: draft
owner: Incident Commander
created: '2024-05-08T09:05:05.477Z'
updated: '2025-12-09T01:55:04.117Z'
tags:
  - postmortem
  - billing-engine
summary: Double Billing Incident 2025-02-05
incident_number: INC-927
severity: SEV-2
incident_date: '2024-08-15'
detection_time: '2024-09-05T08:02:25.860Z'
resolution_time: '2024-01-21T07:45:51.832Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-092
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 5, 2025, a defect in the billing engine's idempotency layer caused a subset of customers to be charged twice for subscription renewal invoices. The issue was triggered by a race condition in the charge-submission worker: when the payment gateway returned an HTTP 502 error, the worker requeued the job without first checking whether the underlying charge had already been created at the gateway. Approximately 214 customers received duplicate charges totaling an estimated $12,000 in erroneous debits.

The incident was detected at 08:02 UTC via a spike in support tickets and a monitoring alert on the billing anomaly dashboard. The duplicate charge job queue was halted at 09:15 UTC, and all affected customers were refunded within four hours. A hotfix was deployed at 11:40 UTC restoring normal billing operations. The follow-on investigation confirmed no charges were lost — only duplicated — and no payment data was exfiltrated.

## Timeline

- **07:45** - Scheduled subscription renewal batch job starts, processing ~1,800 invoices for the February 5 renewal cohort.
- **07:58** - Payment gateway begins intermittently returning HTTP 502 errors; billing worker retries jobs without deduplication check.
- **08:02** - `billing_anomaly_duplicate_charge_rate` alert fires. On-call engineer acknowledges.
- **08:10** - On-call confirms 214 customers have been double-charged; escalates to Billing team lead and Incident Commander.
- **08:22** - Billing charge-submission worker queue is paused to prevent further duplicate charges.
- **08:35** - Engineering confirms root cause: missing idempotency key validation on gateway retry path.
- **09:15** - Duplicate charge queue fully drained; no new double-billing events observed.
- **09:30** - Refund batch initiated for all 214 affected customers via automated refund pipeline.
- **10:45** - Customer support team sends proactive email notification to affected customers.
- **11:40** - Hotfix deployed adding idempotency key check before charge resubmission.
- **12:00** - Billing worker queue re-enabled; normal renewal processing resumes.
- **12:05** - Refund batch confirms all 214 refunds processed successfully.

## Impact

- **Duration**: ~4 hours (07:58 charge duplication begins — 12:05 all refunds confirmed)
- **Customers affected**: 214 customers billed twice for February subscription renewals
- **Financial exposure**: Approximately $12,000 in erroneous duplicate charges, all subsequently refunded
- **Revenue impact**: Zero net revenue loss; processing fees on duplicate transactions estimated at $380 in unrecoverable gateway costs
- **Customer trust**: Elevated support ticket volume (~180 inbound contacts); proactive outreach sent to all affected accounts
- **SLA impact**: Billing accuracy SLA breached for the February 5 renewal cohort

## Root Cause Analysis

1. **Missing idempotency validation on the retry path.** The billing engine submits charges to the payment gateway with a per-invoice idempotency key. However, the retry handler invoked on HTTP 5xx gateway errors did not re-use the original idempotency key — it generated a new one on each retry attempt. This caused the gateway to treat each retry as a distinct new charge rather than a repeat of an in-flight request, resulting in multiple successful charges for a single invoice.

2. **Insufficient gateway error classification.** The worker treated HTTP 502 (Bad Gateway) responses as definitive failures and immediately requeued the job for retry without first querying the gateway's charge-status endpoint to determine whether the original charge had already settled. An HTTP 502 from this gateway can indicate a timeout on an already-committed transaction, making blind retry inherently unsafe.

## Resolution

1. Paused the billing charge-submission worker queue at 08:22 to stop the issuance of any additional duplicate charges.
2. Ran a reconciliation query against the gateway's transaction log to enumerate all invoice IDs with more than one settled charge, producing the definitive list of 214 affected customers.
3. Submitted a bulk refund batch through the automated refund pipeline, issuing a full refund equal to the duplicate charge amount for each affected customer.
4. Deployed a hotfix to the billing worker that enforces idempotency key reuse on all retry attempts and adds a pre-retry status check against the gateway charge-status endpoint before resubmission.
5. Re-enabled the worker queue and processed the remaining February 5 renewal invoices without further issues, confirming the fix was effective.

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Enforce idempotency key reuse on all gateway retry paths across billing engine | Billing Engineering | P1 | 2025-02-12 | Completed |
| Add pre-retry gateway charge-status check to prevent blind resubmission on 5xx errors | Billing Engineering | P1 | 2025-02-12 | Completed |
| Implement `billing_anomaly_duplicate_charge_rate` alert with <0.01% threshold for all charge batches | SRE | P2 | 2025-02-19 | In Progress |
| Update [[SOP-092]] with double-billing detection and emergency queue-pause procedure | On-call Lead | P2 | 2025-02-26 | Pending |
| Conduct end-to-end audit of all billing worker retry handlers for idempotency compliance | Billing Engineering | P3 | 2025-03-05 | Pending |

## Lessons Learned

- **What went well**: The `billing_anomaly_duplicate_charge_rate` alert fired within 4 minutes of the first duplicate charge, enabling rapid containment. The automated refund pipeline allowed all 214 refunds to be issued without manual intervention.
- **What went poorly**: The retry handler had never been tested against a gateway that returns 502 on an already-committed transaction. Integration tests only covered clean failure cases. The gap between the original idempotency key design and the retry implementation existed undetected for over a year.
- **What was lucky**: The payment gateway's idempotency key mechanism correctly deduplicated charges when the key was reused, confirming the fix path immediately. Had the gateway lacked this feature, remediation would have been significantly more complex.
- **Architecture improvement**: All external payment gateway interactions must be wrapped in a gateway-agnostic idempotency guard that survives retries, restarts, and queue redelivery — not just the initial submission path.
- **Process improvement**: Billing batch jobs should have a real-time duplicate charge rate metric visible on the billing operations dashboard before each renewal cohort run, enabling earlier human detection independent of alerting.
