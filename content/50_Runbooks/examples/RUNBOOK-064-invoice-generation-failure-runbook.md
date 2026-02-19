---
id: RUNBOOK-064
type: runbook
title: Invoice Generation Failure Runbook
status: approved
owner: On-Call Engineer
created: '2024-01-02T10:30:16.805Z'
updated: '2025-01-19T21:25:21.051Z'
tags:
  - runbook
  - billing-engine
summary: Invoice Generation Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `billing_invoice_generation_failure_rate_high` - Invoice generation failure rate exceeds 1% for 5 minutes
- `billing_invoice_exception_queue_depth_high` - Invoice exception queue depth exceeds 50 items
- `billing_cycle_run_stalled` - Active billing run has not progressed for 30 minutes
- `billing_invoice_generation_latency_p95_high` - P95 invoice generation latency above 10 seconds for 10 minutes

## Diagnosis Steps

1. **Check the billing run status** - Open the Billing Engine admin console and review the current billing run status. If the run is `IN_PROGRESS`, check how many invoices are in the exception queue. If no run is active, check if the alert is from a single account or a pattern.
2. **Check the invoice generation error logs** - In the log aggregation system, filter by `service:billing-engine` and `event:invoice_generation_failed` for the last 30 minutes. Look for repeated error classes: `UsageDataMissingException`, `TaxCalculationTimeoutException`, `PricingPlanNotFoundException`, or `DatabaseConnectionException`.
3. **Check the tax calculation service** - If errors include `TaxCalculationTimeoutException`, check the tax calculation service health. Verify its error rate and latency in Grafana. A tax service outage will cause all invoices with tax-applicable accounts to fail.
4. **Check the billing database connection pool** - Run `SELECT count(*), state FROM pg_stat_activity WHERE datname = 'billing' GROUP BY state;`. If `active` connections are near the pool max (50), the DB is saturated. Check for long-running queries.
5. **Check for a recent deployment** - Review #billing-deployments for any billing service deployments in the last 60 minutes. If a deploy coincides with the failure onset, rollback is the fastest remediation.

## Remediation Steps

1. **If caused by a recent deploy**: Roll back the billing service per the Deploy Billing Service Update SOP rollback procedure.
2. **If tax calculation service is down**: Enable the tax service circuit breaker flag in the Billing Engine config (`billing.tax.circuit-breaker.enabled=true`). This allows invoice generation to continue with a placeholder tax entry; tax values will be backfilled when the tax service recovers.
3. **If database connection pool is exhausted**: Kill long-running billing queries with `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '5 minutes' AND datname = 'billing' AND state = 'active';`. Restart billing service pods to reset connection state.
4. **If usage data is missing for specific accounts**: Check if the usage aggregation job completed for the affected accounts. Re-trigger aggregation for the affected account IDs via the admin console **Usage > Re-aggregate** function.
5. **If a pricing plan is missing**: Verify the account's plan assignment in the billing admin console. If the plan was deleted or deactivated, restore the plan configuration or assign a valid replacement plan before reprocessing.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks billing run status |
| 10 min | Post initial assessment in #billing-incidents with error class and affected account count |
| 20 min | If failure rate is above 5%: page Billing Platform tech lead via PagerDuty |
| 30 min | If not resolved and billing cycle is blocked: page Engineering Manager, notify Finance Operations |
| 60 min | If billing cycle cannot complete: initiate major incident, assemble war room in #billing-war-room |

## Dashboards

- [Billing Engine Overview](https://grafana.example.com/d/billing-overview) - Invoice generation rate, failure rate, cycle run status
- [Billing Database](https://grafana.example.com/d/billing-db) - Connection pool, query latency, active queries
- [Tax Calculation Service](https://grafana.example.com/d/tax-service) - Error rate, latency, circuit breaker status
- [Billing Event Stream](https://grafana.example.com/d/billing-events) - Event publication rate, consumer lag
- [Billing Logs](https://kibana.example.com/app/discover#/billing) - Full error logs with stack traces
