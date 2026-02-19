---
id: RUNBOOK-052
type: runbook
title: AlertManager Not Firing Runbook
status: approved
owner: On-Call Engineer
created: '2025-11-05T14:46:50.967Z'
updated: '2025-09-22T06:01:45.237Z'
tags:
  - runbook
  - monitoring-stack
summary: AlertManager Not Firing Runbook
example: true
---

## Service

- **System**: [[SYSTEM-039|AlertManager Monitoring System]]
- **Owner team**: Platform / SRE
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #monitoring-ops
- **Runtime**: Kubernetes / AlertManager 0.26.x

## Alerts

- `AlertmanagerDown` - AlertManager pod is not reachable from Prometheus (watchdog alert stops firing)
- `AlertmanagerConfigReloadFailed` - AlertManager failed to reload its configuration
- `AlertmanagerClusterMembersMismatch` - AlertManager cluster has fewer members than expected
- `PrometheusNotConnectedToAlertmanager` - Prometheus cannot connect to any AlertManager instance

## Diagnosis Steps

1. **Check if AlertManager is running** - `kubectl get pods -n monitoring | grep alertmanager`. If pods are not in Running state, check events: `kubectl describe pod alertmanager-0 -n monitoring`.
2. **Check AlertManager health endpoint** - `curl http://alertmanager:9093/-/healthy`. A non-200 response or connection error means AlertManager is down or degraded.
3. **Check Prometheus connection to AlertManager** - Open the Prometheus UI at `Status > Alertmanagers`. Confirm that at least one AlertManager instance shows as `active`. If all show `dropped`, Prometheus cannot reach AlertManager.
4. **Check AlertManager configuration** - Review the AlertManager config for syntax errors: `kubectl exec -n monitoring alertmanager-0 -- amtool check-config /etc/alertmanager/alertmanager.yml`. Config errors cause silent failures where alerts are received but not routed.
5. **Check for active silences** - `kubectl exec -n monitoring alertmanager-0 -- amtool silence query`. An overly broad silence rule may be suppressing all alerts. Check for wildcards in the matchers.
6. **Check route configuration** - Verify that the alert's labels match at least one route in the routing tree. Use `amtool config routes test --config.file=/etc/alertmanager/alertmanager.yml {label=value}` to test routing.

## Remediation Steps

1. **If AlertManager pod is crashlooping**: Check the pod logs for the reason. Common causes are config file syntax errors or missing secrets. Fix the root cause before restarting.
2. **If config reload failed**: Roll back the most recent AlertManager config change from the monitoring repository. The GitOps pipeline will redeploy the previous working config.
3. **If Prometheus cannot connect to AlertManager**: Verify the AlertManager service is reachable from within the cluster. Check NetworkPolicy rules in the monitoring namespace that may be blocking Prometheus egress.
4. **If alerts are being silenced unexpectedly**: List active silences and expire any that are incorrectly matching production alerts: `amtool silence expire {silence-id}`.
5. **If the routing tree is missing a required route**: Add the missing route per SOP-076 and verify it routes correctly to the intended receiver before deploying to production.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks AlertManager pod health and connectivity |
| 10 min | Post status in #monitoring-ops; if AlertManager is down, all production alerts are dark |
| 20 min | If not resolved: page Platform Lead; this is a P1 monitoring blind-spot |
| 30 min | If still down: page Engineering Manager; manually monitor production dashboards until restored |

## Dashboards

- [AlertManager Self-Monitoring](https://grafana.example.com/d/alertmanager-self) - Alert receive rate, notifications sent, silences active
- [Platform Health Overview](https://grafana.example.com/d/platform-health) - Overall monitoring stack component health
- [Prometheus Targets](https://grafana.example.com/d/prometheus-targets) - Prometheus connectivity to AlertManager and all scrape targets
