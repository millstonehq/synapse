---
id: RUNBOOK-048
type: runbook
title: Deployment Pipeline Timeout Runbook
status: approved
owner: On-Call Engineer
created: '2024-07-21T17:00:24.853Z'
updated: '2026-05-01T21:02:38.160Z'
tags:
  - runbook
  - ci-cd-platform
summary: Deployment Pipeline Timeout Runbook
example: true
---

## Service

- **System**: [[SYSTEM-033|Deployment Pipeline]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: ArgoCD / Kubernetes / GitHub Actions

## Alerts

- `DeploymentPipelineTimeoutExceeded` — A deployment pipeline job has exceeded its configured timeout value and been cancelled by the CI platform; the deployment did not complete
- `KubernetesRolloutProgressDeadlineExceeded` — A Kubernetes Deployment rollout has exceeded its `progressDeadlineSeconds` without all replicas reaching the ready state
- `DeploymentWaitForHealthyTimeout` — A post-deployment health check step has waited more than 15 minutes for the service to report healthy, suggesting a readiness probe issue

## Diagnosis Steps

1. **Identify the pipeline stage that timed out** - Review the deployment pipeline logs to find which specific step exceeded the timeout: image push, manifest apply, rollout wait, or post-deploy health check.
2. **Check Kubernetes rollout status** - Run `kubectl rollout status deploy/<service-name> -n <namespace>` to see the current rollout state; identify whether pods are pending, crashlooping, or stuck in "ContainerCreating."
3. **Inspect pod events** - Run `kubectl describe pod -l app=<service-name> -n <namespace>` and review the Events section for image pull failures, resource constraint violations, or liveness probe failures.
4. **Check readiness probe configuration** - If the rollout is stuck waiting for pods to become ready, verify the readiness probe endpoint is responding correctly on the new pod version; exec into a pod and test manually.
5. **Check cluster resource availability** - Run `kubectl describe nodes` to verify sufficient CPU and memory is available on cluster nodes; resource pressure can cause pods to be stuck in "Pending."

## Remediation Steps

1. **If pods are stuck pulling the image**: Verify the container registry is accessible from the cluster; check image pull secrets are valid and the image tag exists in the registry.
2. **If pods are crashlooping**: Review the pod logs (`kubectl logs -p <pod>` for previous container logs); the deployment likely has a startup error — roll back immediately to the previous version.
3. **If pods are stuck in "Pending" due to resource pressure**: Check whether node autoscaling is provisioning additional nodes; if not, manually scale up the node group or reduce the deployment's resource requests temporarily.
4. **If the readiness probe is failing**: Check whether the application requires a longer startup time than the `initialDelaySeconds` allows; increase the delay in the manifest and redeploy, or roll back if the application has a startup failure.
5. **If the timeout was due to a slow image push**: Investigate registry latency on the push side; re-trigger the pipeline during lower-traffic hours or split the image into smaller layers to reduce push time.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer identifies timed-out pipeline stage |
| 10 min | If pods are crashlooping, initiate rollback immediately |
| 20 min | If cluster-level resource issue, escalate to Platform Engineer |
| 45 min | If deployment cannot be completed or rolled back cleanly, declare incident and escalate to Platform Lead |

## Dashboards

- [Deployment Pipeline Status](https://grafana.internal/d/deploy-pipelines) - Active deployments, stage durations, and timeout events
- [Kubernetes Rollout Health](https://grafana.internal/d/k8s-rollouts) - Rollout progress, pod readiness, and restart counts
- [Cluster Resource Utilization](https://grafana.internal/d/cluster-resources) - Node CPU/memory headroom and pending pod counts
