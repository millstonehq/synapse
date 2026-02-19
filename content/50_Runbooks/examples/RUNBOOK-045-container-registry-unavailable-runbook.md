---
id: RUNBOOK-045
type: runbook
title: Container Registry Unavailable Runbook
status: review
owner: On-Call Engineer
created: '2025-03-11T21:30:15.737Z'
updated: '2026-03-04T00:33:43.327Z'
tags:
  - runbook
  - ci-cd-platform
summary: Container Registry Unavailable Runbook
example: true
---

## Service

- **System**: [[SYSTEM-032|Container Registry]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: Harbor / AWS ECR / GCP Artifact Registry

## Alerts

- `ContainerRegistryHealthCheckFailed` — The registry health endpoint `/v2/` is returning non-200 responses or timing out; all push and pull operations will fail
- `ContainerRegistryPushLatencyHigh` — P95 push latency exceeds 30 seconds for 5 consecutive minutes, indicating storage or network degradation
- `ContainerRegistryPullErrorRate` — Pull error rate exceeds 5% over a 3-minute window, blocking deployments and CI builds that pull base images

## Diagnosis Steps

1. **Confirm registry unavailability** - From a runner host or deployment node, run `curl -I https://registry.internal/v2/` and note the HTTP status code and response time; distinguish between total unavailability (5xx, timeout) and authentication failures (401).
2. **Check registry service status** - If using a managed registry (ECR, GCR), check the cloud provider's status page for the relevant region; for self-hosted Harbor, check the Harbor UI and the Harbor pod status in Kubernetes.
3. **Check registry storage backend** - For self-hosted registries, check the object storage backend (S3, GCS) for service disruptions; run `aws s3 ls s3://<registry-bucket>/` to confirm object storage is accessible.
4. **Review registry logs** - Tail the registry container logs (`kubectl logs -n registry deploy/registry -f --tail=100`) for authentication errors, storage errors, or database connection failures.
5. **Check registry database** - For Harbor, verify the PostgreSQL backend is healthy and accepting connections; check for locks or long-running queries that may be blocking registry operations.

## Remediation Steps

1. **If the managed registry (ECR/GCR) is having a regional outage**: Communicate to engineering teams to pause deployments; enable the registry mirror/cache if configured to serve cached pulls for in-flight builds.
2. **If the self-hosted registry pod is crashlooping**: Describe the pod for error details (`kubectl describe pod`), check resource limits, and restart the deployment (`kubectl rollout restart deploy/registry -n registry`).
3. **If storage backend is exhausted**: Follow the Handle Container Registry Quota SOP to clean up old images and reclaim space.
4. **If authentication service (Notary/token endpoint) is down**: Restart the authentication service pod; if the registry is inaccessible due to expired TLS certificates, rotate certificates per the certificate rotation procedure.
5. **If only push operations are failing and pulls work**: Check registry storage write permissions and object storage write credentials; restart only the push-handling registry replicas.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms outage and begins diagnosis |
| 10 min | Notify #platform-incidents of registry outage; advise teams to pause deployments |
| 20 min | Escalate to Platform Engineer if self-hosted registry cannot be restored |
| 45 min | Engage cloud provider support if managed registry outage exceeds SLA; escalate to Platform Lead |

## Dashboards

- [Registry Health](https://grafana.internal/d/registry-health) - Push/pull success rates, latency, and error breakdown
- [Registry Storage](https://grafana.internal/d/registry-storage) - Storage utilization and quota consumption
- [Deployment Blocker Status](https://grafana.internal/d/deploy-blockers) - Active pipeline failures attributable to registry errors
