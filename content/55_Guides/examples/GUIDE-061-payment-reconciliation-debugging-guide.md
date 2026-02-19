---
id: GUIDE-061
type: guide
title: Payment Reconciliation Debugging Guide
status: accepted
owner: Developer Experience
created: '2025-04-07T14:14:45.365Z'
updated: '2026-05-11T11:38:07.216Z'
tags:
  - guide
  - payment-processing
summary: Payment Reconciliation Debugging Guide
audience: internal
related_systems:
  - SYSTEM-001
  - SYSTEM-005
related_sops:
  - SOP-007
  - SOP-002
example: true
---

## Why This Matters

Payment reconciliation failures are silent by nature. Unlike a 5xx error rate spike that fires an alert within minutes, a reconciliation discrepancy may not be noticed until the finance team reviews reports the next morning — or, in the worst case (INC-75), 6 hours after the nightly batch completed. This guide explains how to diagnose and resolve the most common reconciliation issues.

For the runbook version of this (shorter, action-oriented), see [[SOP-007|Settlement Reconciliation SOP]]. This guide covers the underlying concepts so you understand why each diagnostic step works.

## The Mental Model

Reconciliation discrepancies fall into three categories:

1. **Timing discrepancies**: A transaction is in our system but not yet in the gateway's settlement report (or vice versa). These resolve themselves within 24-48 hours and do not require action.
2. **Amount discrepancies**: A transaction's settled amount differs from its captured amount. These are always bugs or fraud — they require investigation.
3. **Missing records**: A transaction appears in the gateway report but not in our `payments` table, or vice versa. These are always serious and require immediate investigation.

## How Reconciliation Works

The [[SYSTEM-001|Payment Gateway Service]] processes authorization and capture operations in real time. Settlement happens separately: each night, Stripe generates a settlement CSV containing all transactions that settled on that day. The [[SYSTEM-005|Payment Webhook Dispatcher]] (which also handles settlement) processes this CSV and updates matching payment records from `captured` to `settled`.

The reconciliation process matches records on `gateway_ref` (our name for Stripe's `charge_id`). If a record in the CSV doesn't match any `payments` row by `gateway_ref`, that's a missing record discrepancy.

## Diagnosing a Timing Discrepancy

**Symptom**: Finance sees transactions stuck in `captured` state on the daily dashboard.

**Query to check** (run on the analytics replica):
```sql
SELECT id, gateway_ref, amount, currency, state, created_at
FROM payments
WHERE state = 'captured'
AND created_at < now() - interval '2 days'
ORDER BY created_at;
```

If this returns rows, the settlement batch either missed these transactions or they haven't settled in Stripe yet.

**Next steps**:
1. Check the Stripe dashboard for the `charge_id` (our `gateway_ref`). If it shows as "Paid" in Stripe but our record is still `captured`, the settlement batch missed it.
2. Check the settlement batch logs for the relevant date: filter Kibana by `service:settlement-batch` and `date:YYYY-MM-DD`.
3. If the batch ran but missed the transaction, it may be in the DLQ. Check: `aws sqs get-queue-attributes --queue-url [DLQ_URL] --attribute-names ApproximateNumberOfMessages`.

## Diagnosing a Missing Record Discrepancy

**Symptom**: Stripe settlement CSV has a charge ID that doesn't exist in our `payments` table.

**This should never happen in normal operation.** Potential causes:
- The payment was created directly in Stripe (bypassing our API) — check Stripe dashboard for the charge's metadata
- A database migration lost rows (check DB backup and pg_audit logs)
- The charge is from a test mode key accidentally used in production (check Stripe mode in the charge's dashboard URL)

**Query to verify** (run on primary):
```sql
SELECT COUNT(*) FROM payments WHERE gateway_ref = 'ch_XXXXX';
```

If this returns 0 and the charge exists in Stripe, page the Payments tech lead immediately.

## Diagnosing an Amount Discrepancy

**Symptom**: A transaction's `amount` in our database differs from the `amount_captured` in the Stripe settlement CSV.

**Most common causes**:
- Partial capture: We captured a different amount than what was authorized. Check `payment_events` for a `captured` event with an `amount` field that differs from the original authorization.
- Currency conversion rounding: For multi-currency transactions, minor-unit conversion may have introduced a 1-unit rounding difference. This is a known edge case for currencies with non-standard decimal places.
- Refund applied to settlement: Stripe deducts refunds from the settlement total. Our batch may not be handling refund offsets correctly.

**Query to find amount discrepancies** (requires importing the settlement CSV):
```sql
SELECT p.id, p.gateway_ref, p.amount AS our_amount, s.amount_captured AS stripe_amount
FROM payments p
JOIN settlement_import s ON p.gateway_ref = s.charge_id
WHERE p.amount != s.amount_captured;
```

## Common Questions

### "The settlement batch ran but the transactions are still `captured` — what happened?"

Check if the SQS DLQ ARN is correct (this was the root cause of INC-75). Run: `aws sqs get-queue-attributes --queue-url [SETTLEMENT_DLQ_URL]`. If the queue doesn't exist or the ARN is wrong, the batch is silently dropping state-change messages.

### "How do I manually re-settle a batch of transactions?"

Use the settlement replay script: `./scripts/replay-settlement.sh --date YYYY-MM-DD --dry-run` first, then remove `--dry-run` after verifying the output. This re-reads the Stripe CSV for that date and reprocesses all state changes. See [[SOP-007|Settlement Reconciliation SOP]] for the exact procedure.

### "How many discrepancies is normal?"

Our target is < 0.01% of daily transactions. Currently we see ~0.03%. All discrepancies that are not timing-related (resolving within 48 hours) must be investigated and documented within the monthly reconciliation report.

## Next Steps

- For immediate incident response, use [[SOP-007|Settlement Reconciliation SOP]]
- For understanding the settlement batch architecture, review [[SYSTEM-005|Payment Webhook Dispatcher]] system doc
- For the payment gateway's role in authorization and capture, see [[SYSTEM-001|Payment Gateway Service]] system doc
