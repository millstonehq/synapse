---
id: RUNBOOK-034
type: runbook
title: Search Service Out of Memory Runbook
status: approved
owner: On-Call Engineer
created: '2024-06-12T12:38:07.442Z'
updated: '2026-10-30T08:36:45.337Z'
tags:
  - runbook
  - search-platform
summary: Search Service Out of Memory Runbook
example: true
---

## Service

- **System**: [[SYSTEM-021|Search Query Service]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Node.js 20 / 4GB container memory limit

## Alerts

- `search_service_oom_killed` - Search service pod has been OOM-killed by Kubernetes (exit code 137)
- `search_service_pod_crashloop` - Search service pod is restarting more than 3 times in 10 minutes
- `search_service_memory_high` - Container memory usage exceeds 90% of limit for more than 5 minutes

## Diagnosis Steps

1. **Confirm OOM kill** - Run `kubectl describe pod <pod-name> -n search` and look for `OOMKilled` in the last state section. Note the time of the OOM kill to correlate with traffic or query patterns at that time.
2. **Check memory usage trend** - Review Grafana container memory usage for the affected pods over the past 2 hours. Look for a steady memory leak trend (gradual increase to OOM) versus a sudden spike (triggered by a specific query or traffic event).
3. **Check for memory leak indicators** - Review the search service application logs for the period before the OOM kill. Look for warnings about large result set processing, unbounded caches, or heap dumps if the application was configured to write one before exit.
4. **Check for traffic volume anomaly** - Review QPS at the time of the OOM kill on Grafana. A sudden traffic spike can exhaust memory even without a code leak if the service is under-provisioned for peak load.
5. **Check recent deploys** - A new code deployment within the past 24 hours is a likely cause of newly introduced memory leaks. Check #search-deployments for recent changes.

## Remediation Steps

1. **If the pod is in CrashLoopBackOff and service is degraded**: Temporarily increase the pod count to maintain availability while the root cause is investigated: `kubectl scale deployment search-api -n search --replicas=6`.
2. **If caused by a recent deploy**: Roll back the deployment immediately. OOM conditions from code changes are unlikely to resolve without a rollback.
3. **If caused by a traffic spike exceeding memory capacity**: Scale out the deployment to distribute memory load: `kubectl scale deployment search-api -n search --replicas=8`. Set a horizontal pod autoscaler if one is not already configured.
4. **If caused by a memory leak in a known component (e.g., result caching layer)**: Implement a temporary fix by restarting pods on a rolling schedule to clear accumulated memory before OOM is reached: `kubectl rollout restart deployment/search-api -n search`.
5. **If root cause is unknown**: Enable memory profiling in the next deployment, set memory limits higher by 50% as a temporary measure, and schedule a post-incident engineering investigation within 48 hours.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms OOM kill and checks pod count |
| 10 min | Post status in #search-incidents; confirm search is still serving |
| 20 min | If pods are repeatedly OOM-killing: page Search Platform tech lead |
| 40 min | If search availability is below SLO: page Engineering Manager |
| 60 min | If no root cause is identified: escalate to senior engineer for memory profiling |

## Dashboards

- [Search Service Memory](https://grafana.example.com/d/search-service-memory) - Container memory usage, OOM kill events, pod restart count
- [Search Query Performance](https://grafana.example.com/d/search-query-perf) - QPS, error rate, latency at time of OOM events
- [Kubernetes Search Namespace](https://grafana.example.com/d/k8s-search) - Pod health, resource limits vs usage
