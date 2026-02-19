---
id: RUNBOOK-067
type: runbook
title: Tax Calculation Service Failure Runbook
status: approved
owner: On-Call Engineer
created: '2025-03-16T12:47:35.210Z'
updated: '2026-03-22T22:24:06.155Z'
tags:
  - runbook
  - billing-engine
summary: Tax Calculation Service Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `tax_service_error_rate_high` - Tax calculation service error rate exceeds 5% for 3 minutes
- `tax_service_latency_p95_high` - Tax calculation service P95 latency above 3 seconds for 5 minutes
- `tax_service_pod_crashloop` - Tax service pod restarting more than 3 times in 10 minutes
- `billing_invoice_tax_calculation_failure_rate_high` - Invoice generation failures attributed to tax service exceeding 2%

## Diagnosis Steps

1. **Check the tax service pod health** - Run `kubectl get pods -n billing -l app=tax-service`. Check for pods in `CrashLoopBackOff` or `Error` state. If all pods are unhealthy, this is a full tax service outage.
2. **Check the tax service error logs** - Filter logs by `service:tax-service` and `level:error`. Look for: `NullPointerException` on jurisdiction lookup (missing jurisdiction data), `TaxRateNotFoundException` (jurisdiction code not in tax rate table), or `DatabaseConnectionException`.
3. **Check the tax rate table** - Connect to the billing database and verify the tax rate table has entries for the jurisdictions being requested: `SELECT count(*) FROM tax_rates WHERE effective_date <= NOW();`. A count of 0 indicates the table is empty or not loaded.
4. **Check if a tax rate update was recently applied** - Review #billing-operations for any tax rate updates in the last 24 hours. An incorrect rate update may be causing validation failures in the tax service.
5. **Check downstream impact on billing** - On the Billing Engine Overview dashboard, check if invoice generation failure rate has increased. A tax service failure will cause all invoices requiring tax calculation to fail.

## Remediation Steps

1. **If tax service pods are crashing**: Review the pod logs for the crash reason. If it is a startup configuration issue, check the tax service ConfigMap for recent changes: `kubectl describe configmap tax-service-config -n billing`. Revert any recent config changes.
2. **If the tax rate table is empty**: The tax service requires data. Restore the tax rate data from the most recent backup: run the `tax-rate-restore.sh` script from the billing ops toolbox pointing to the latest backup. Restart tax service pods after restore.
3. **Enable the billing service circuit breaker**: If the tax service is down and the billing cycle cannot wait, enable the tax calculation circuit breaker in the billing service: `kubectl set env deployment/billing-service -n billing BILLING_TAX_CIRCUIT_BREAKER=true`. This generates invoices with a tax placeholder; Finance Operations must be notified.
4. **If a recent tax rate update caused the issue**: Revert the tax rate update following the Run Tax Rate Update SOP rollback procedure. Restart tax service pods after reverting.
5. **If tax service is degraded but partially functional**: Scale up tax service replicas to handle the load: `kubectl scale deployment/tax-service -n billing --replicas=4`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks pod health and tax service error rate |
| 10 min | Post impact assessment in #billing-incidents: error rate, affected invoice count, phase of billing cycle |
| 20 min | If circuit breaker is being enabled: notify Finance Operations immediately |
| 30 min | If tax service cannot be restored: page Engineering Manager |
| 60 min | If billing cycle is blocked: initiate major incident process |

## Dashboards

- [Tax Calculation Service](https://grafana.example.com/d/tax-service) - Error rate, latency, request volume, circuit breaker status
- [Billing Engine Overview](https://grafana.example.com/d/billing-overview) - Invoice generation failure rate attributed to tax service
- [Kubernetes Billing Namespace](https://grafana.example.com/d/k8s-billing) - Tax service pod health, restarts, resource usage
- [Tax Service Logs](https://kibana.example.com/app/discover#/tax-service) - Error logs with jurisdiction codes and failure reasons
