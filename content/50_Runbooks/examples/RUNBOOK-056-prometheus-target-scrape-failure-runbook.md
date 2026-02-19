---
id: RUNBOOK-056
type: runbook
title: Prometheus Target Scrape Failure Runbook
status: approved
owner: On-Call Engineer
created: '2024-01-31T15:44:29.428Z'
updated: '2025-05-06T02:40:51.742Z'
tags:
  - runbook
  - monitoring-stack
summary: Prometheus Target Scrape Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-036|Prometheus Monitoring System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / Prometheus 2.x

## Alerts

- `PrometheusTargetScrapeFailure` - A Prometheus scrape target has been failing for more than 10 minutes
- `PrometheusTargetMissing` - A previously present scrape target is no longer discoverable
- `PrometheusScrapeSlowness` - Scrape duration for a target exceeds 10 seconds consistently
- `PrometheusJobScrapeMissRatioHigh` - More than 10% of targets in a scrape job are failing

## Diagnosis Steps

1. **Identify the failing targets** - Open the Prometheus UI at `Status > Targets`. Filter by state=down. Note the target URL, the `job` label, and the error message shown in the `Last error` column.
2. **Check if the target service is running** - For Kubernetes service discovery targets, verify the backing pod is running: `kubectl get pods -n {namespace} -l {selector}`. A missing pod means the service is down, not a scrape configuration problem.
3. **Attempt a manual scrape** - From within the monitoring namespace, curl the target's metrics endpoint directly: `kubectl exec -n monitoring prometheus-0 -- curl -s http://{target-address}/metrics | head -20`. This isolates whether the issue is network/auth or a missing endpoint.
4. **Check for certificate or auth errors** - If the scrape target requires TLS or bearer token auth, the `Last error` field will indicate a certificate error or 401/403. Verify the scrape secret is current and correct.
5. **Check Kubernetes service discovery** - If targets are disappearing, check whether the `ServiceMonitor` or `PodMonitor` CRD still matches the target's current labels: `kubectl get servicemonitor -n {namespace} -o yaml`.

## Remediation Steps

1. **If the target service pod is down**: This is a service health issue, not a monitoring issue. Page the service owner and follow their runbook. The scrape failure will auto-resolve when the pod recovers.
2. **If the metrics endpoint is missing from the target**: The service may have removed its `/metrics` endpoint in a recent deploy. Notify the service team. Temporarily silence the scrape failure alert while they fix the endpoint.
3. **If it is an auth or TLS error**: Rotate the scrape secret if expired (follow SOP-079), or update the ServiceMonitor's TLS configuration to match the target's current certificate.
4. **If the ServiceMonitor label selector no longer matches**: Update the ServiceMonitor's selector to match the service's current labels. Submit a PR to the monitoring configuration repository.
5. **If a large number of targets in a job are failing simultaneously**: This may indicate a network policy change blocking Prometheus egress, or a namespace-wide issue. Check NetworkPolicies in the target namespace.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies the failing targets and checks service health |
| 10 min | Post findings in #monitoring-ops: target name, error type, affected service team notified |
| 20 min | If widespread scrape failure (>10 targets): page Platform Lead |
| 45 min | If Prometheus cannot scrape critical services for >30 min: escalate to Engineering Manager |

## Dashboards

- [Prometheus Targets](https://grafana.example.com/d/prometheus-targets) - Target up/down status, scrape duration, miss rate by job
- [Prometheus Self-Monitoring](https://grafana.example.com/d/prometheus-self) - Overall scrape health and target discovery
- [Platform Health Overview](https://grafana.example.com/d/platform-health) - Overall monitoring stack component health
