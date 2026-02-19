---
id: RUNBOOK-080
type: runbook
title: Billing Proration Calculation Error Runbook
status: draft
owner: On-Call Engineer
created: '2025-05-30T17:13:56.967Z'
updated: '2026-01-20T01:31:09.873Z'
tags:
  - runbook
  - billing-engine
summary: Billing Proration Calculation Error Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Event Processor]]
- **Owner team**: Billing Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Python 3.12 / PostgreSQL 16 / Redis 7

## Alerts

- `billing_proration_error_rate_high` - Proration calculation error rate exceeds 1% of plan change requests for 5 minutes
- `billing_proration_ledger_imbalance` - A proration ledger entry debit/credit pair does not sum to zero (immediate page)
- `billing_proration_stripe_sync_failed` - Proration adjustment failed to sync to Stripe for more than 3 retries
- `billing_proration_preview_latency_high` - P95 latency for the proration preview endpoint exceeds 2 seconds for 5 minutes

## Diagnosis Steps

1. **Check for a recent Billing Engine deploy** - Look at #deployments and the ArgoCD dashboard for the `billing-engine` namespace. If the alert started within 30 minutes of a deploy, skip to Remediation Step 1 (rollback).
2. **Check proration error logs** - In Kibana, filter by `service:billing-engine` and `component:proration` and `level:error`. Look for: `PlanChangeNotFound` (plan IDs in the event do not exist in the plan catalog), `PeriodDateError` (invalid period date such as `period_end` before `period_start`), `StripeRateLimitError` (Stripe proration sync throttled).
3. **Check for ledger imbalance** - Run on billing PostgreSQL: `SELECT id, debit_cents - credit_cents AS imbalance FROM proration_ledger_entries WHERE debit_cents != credit_cents ORDER BY created_at DESC LIMIT 20;`. Any non-zero rows are a critical data integrity issue requiring immediate escalation.
4. **Check Stripe proration sync queue** - Inspect the RabbitMQ `billing.proration.stripe-sync` queue depth in the RabbitMQ management console. If messages are backing up, the Stripe sync worker may be failing or rate-limited.
5. **Validate a specific proration** - Use the preview endpoint to re-compute for the affected subscription: `POST /internal/v1/proration/preview` with the plan change details. Compare the result to what is recorded in `proration_ledger_entries`.

## Remediation Steps

1. **If caused by a recent deploy**: Roll back the `billing-engine` deployment in ArgoCD immediately. Do not attempt fix-forward for proration errors — an incorrect proration that charges a customer incorrectly requires a manual credit note and Finance notification.
2. **If PlanChangeNotFound errors**: The plan ID in the change event does not exist in the plan catalog. Pause the affected billing runs. Notify Billing Engineering to investigate the plan catalog inconsistency before resuming.
3. **If ledger imbalance detected**: This is a critical data integrity error. Page the Billing Tech Lead immediately. Halt all billing runs by setting `billing_run_processor_paused=true` in the feature flag system. Do not attempt automated remediation. Manual ledger correction requires Finance sign-off.
4. **If Stripe sync is failing**: Check `status.stripe.com`. If Stripe is healthy, verify the Stripe secret key in Kubernetes Secrets (`kubectl get secret billing-stripe-secret -n billing -o yaml`). Check for recent key rotation in the Stripe dashboard.
5. **If proration preview latency is high**: Check PostgreSQL for slow queries with `SELECT pid, query, now() - query_start AS duration FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC LIMIT 10;`. Likely cause: missing index on `billing_period_aggregates(subscription_id, period_start, period_end)`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call acknowledges; begin diagnosis in #billing-incidents |
| 15 min | If not resolved: page Billing Tech Lead via PagerDuty schedule "billing-leads" |
| 30 min | If ledger imbalance: halt all billing runs; page Engineering Manager; notify Finance |
| 60 min | If not resolved: initiate major incident process; assess customer billing impact |

## Dashboards

- [Billing Engine Overview](https://grafana.example.com/d/billing-overview) - Invoice error rates, proration latency, billing run throughput
- [Billing Proration](https://grafana.example.com/d/billing-proration) - Proration success/failure rate, Stripe sync queue depth, ledger balance checks
- [Billing Ledger Integrity](https://grafana.example.com/d/billing-ledger) - Ledger balance invariant monitor, imbalance alerts
- [Billing Engine Logs](https://kibana.example.com/app/discover#/billing) - Structured error logs with proration context fields
- [Billing RabbitMQ](https://grafana.example.com/d/billing-rabbitmq) - Queue depths for billing run and Stripe sync queues
