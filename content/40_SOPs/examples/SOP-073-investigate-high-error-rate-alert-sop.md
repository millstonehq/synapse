---
id: SOP-073
type: sop
title: Investigate High Error Rate Alert SOP
status: review
owner: DevOps Lead
created: '2025-02-01T16:17:33.953Z'
updated: '2026-05-08T16:05:56.307Z'
tags:
  - sop
  - monitoring-stack
summary: Investigate High Error Rate Alert SOP
related_process: PROCESS-045
related_systems:
  - SYSTEM-040
example: true
---

## Preconditions

- A high error rate alert has fired (typically `{service}_error_rate_critical` or similar)
- You have acknowledged the PagerDuty alert and posted in the incident channel
- You have access to Grafana, the log aggregation system, and the deployment history

## Materials/Access

- Grafana access showing the service's error rate panel and breakdown by endpoint
- Log aggregation system (Loki or Elasticsearch) with the ability to filter by service and log level
- Jaeger access for querying error traces by HTTP status code
- Deployment history for the affected service (deployments Slack channel or CI/CD system)
- Access to the service's Kubernetes namespace for pod status checks

## Procedure

1. Open the service's Grafana overview dashboard and note the current error rate, which endpoints are affected (use the per-endpoint breakdown panel), and when the error rate started rising.
2. Check the deployments channel for any deployments of this service in the last 2 hours. If a deploy happened close to the onset time, treat it as the likely cause and skip to step 7.
3. Open the log aggregation system and filter for `level:error` or `level:fatal` for the affected service in the last 30 minutes. Look for patterns: is it one error type dominating? Is it one endpoint?
4. Note the most frequent error messages. Common patterns to look for: HTTP 500 responses (code bug), connection timeouts to database or dependencies, and out-of-memory panics.
5. Open Jaeger and search for error traces for the service in the last 15 minutes. Click into a sample failed trace to see which span is failing and what the error message is.
6. Check the service's pod status: `kubectl get pods -n {namespace}` to see if any pods are crash-looping or have recent restarts.
7. If the cause is a recent deploy: notify the incident channel and begin rollback immediately. Error rate investigation can wait until after rollback.
8. If the cause is a dependency failure: check the dependency's dashboard and status page. Notify the dependency team.
9. Apply the remediation identified and monitor the error rate on the Grafana dashboard until it returns below the alert threshold.

## Validation

- Error rate has dropped below the alert threshold on the Grafana dashboard
- No new error traces are appearing in Jaeger for the same failure mode
- The root cause has been identified and documented in the incident channel
- If remediation involved a rollback, the previous version is confirmed running in the deployment dashboard

## Rollback

1. If the investigation steps caused any configuration or deployment changes, revert them before escalating.
2. If no root cause has been found after 15 minutes of investigation, escalate to team lead immediately.
3. If the error rate continues rising despite remediation attempts, declare P1 and invoke the Incident Commander process.
4. Post a rollback summary in the incident channel including what was reverted and the current error rate status.
