---
id: RUNBOOK-046
type: runbook
title: ArgoCD Sync Failure Runbook
status: deprecated
owner: On-Call Engineer
created: '2024-08-02T19:31:46.053Z'
updated: '2025-08-15T17:17:02.153Z'
tags:
  - runbook
  - ci-cd-platform
summary: ArgoCD Sync Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-033|ArgoCD]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: Kubernetes / ArgoCD

## Alerts

- `ArgoCDApplicationSyncFailed` — An ArgoCD Application has been in "OutOfSync" state for more than 10 minutes after a sync attempt; the desired state has not been applied to the cluster
- `ArgoCDApplicationDegraded` — An ArgoCD Application is in "Degraded" health state, indicating Kubernetes resources are not healthy after a sync
- `ArgoCDSyncQueueBacklog` — ArgoCD sync queue has more than 20 pending applications, suggesting controller overload or cluster API server degradation

## Diagnosis Steps

1. **Identify the failing application** - Open the ArgoCD UI or run `argocd app list` and filter for applications in "OutOfSync" or "Degraded" state; note the application name, namespace, and last sync timestamp.
2. **Check sync error details** - Click on the application in the ArgoCD UI and navigate to the "Sync Status" tab; read the full error message, which typically indicates the specific Kubernetes resource that failed to apply.
3. **Check Kubernetes resource status** - Run `kubectl describe <resource-type>/<resource-name> -n <namespace>` for the resource mentioned in the sync error; look for admission webhook rejections, resource quota violations, or missing dependencies.
4. **Check ArgoCD controller logs** - Run `kubectl logs -n argocd deploy/argocd-application-controller --tail=100` and filter for the failing application name; look for permission errors or API server connectivity issues.
5. **Verify the target manifest is valid** - Check the source GitOps repository to confirm the manifest file that triggered the sync is syntactically valid and contains no templating errors.

## Remediation Steps

1. **If the sync failure is a Kubernetes admission webhook rejection**: Identify which webhook is rejecting the resource (visible in the error message); either fix the manifest to comply with the webhook policy or escalate to the security team if the policy needs adjustment.
2. **If the sync failure is a resource quota violation**: Check namespace resource quotas (`kubectl describe resourcequota -n <namespace>`); request a quota increase or reduce the resource requests in the manifest.
3. **If the sync failure is a manifest syntax error**: Fix the YAML in the GitOps repository, push the corrected manifest, and trigger a new sync from the ArgoCD UI.
4. **If the application is degraded due to failed pod scheduling**: Check for node selector mismatches, missing node capacity, or PersistentVolumeClaim binding failures; resolve the scheduling constraint before re-syncing.
5. **If ArgoCD itself is overloaded**: Reduce the sync concurrency setting in the ArgoCD ConfigMap and restart the application controller; investigate whether the queue backlog is caused by a runaway sync loop.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer diagnoses sync failure root cause |
| 15 min | If multiple applications are failing simultaneously, escalate to Platform Engineer |
| 30 min | If production deployments are blocked, declare a deployment platform incident |
| 60 min | If ArgoCD requires reinstallation or cluster-level intervention, escalate to Platform Lead |

## Dashboards

- [ArgoCD Application Status](https://argocd.internal/applications) - Live view of all application sync and health states
- [ArgoCD Metrics](https://grafana.internal/d/argocd-metrics) - Sync success rate, queue depth, and reconciliation latency
- [Kubernetes Cluster Health](https://grafana.internal/d/k8s-cluster) - Node availability, resource quota utilization, and API server latency
