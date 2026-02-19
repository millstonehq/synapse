---
id: GUIDE-039
type: guide
title: Implementing Blue-Green Deployments
status: approved
owner: Engineering Team
created: '2024-11-25T00:56:32.471Z'
updated: '2026-02-19T08:55:34.820Z'
tags:
  - guide
  - ci-cd-platform
summary: Implementing Blue-Green Deployments
audience: internal
related_systems:
  - SYSTEM-031
example: true
---

## What is Blue-Green and When Should You Use It

Blue-green deployment is a release strategy where two identical production environments — "blue" (current live) and "green" (new version) — run in parallel. Traffic is switched from blue to green atomically at the load balancer level once the green environment has been validated. If green has problems, rollback is instant: flip the traffic back to blue.

Use blue-green when:
- Your service handles stateless HTTP/gRPC traffic and can be switched at the ingress level
- You need near-zero downtime for deployments (connection draining handles in-flight requests)
- You want rollback to be a seconds-level operation rather than a minutes-level rollout reversal
- Your service can run two versions concurrently without schema incompatibilities

Do not use blue-green for services with database migrations that are not backward-compatible with the previous version, or for services that maintain long-lived stateful connections that would be disrupted by an abrupt traffic cut.

## Prerequisites

Before implementing blue-green, confirm your service meets these requirements:

- The service is deployed on Kubernetes and managed by a GitOps controller (ArgoCD)
- An Ingress or Gateway API resource controls external traffic routing for the service
- The service exposes a health check endpoint that returns 200 only when fully ready to serve traffic
- You have tested that two versions of the service can run concurrently without causing database or cache conflicts

## Configuring Blue-Green in ArgoCD

The ArgoCD Rollouts controller provides native blue-green support. Add a `Rollout` resource to your service's GitOps manifests as a replacement for the standard `Deployment` resource:

```yaml
spec:
  strategy:
    blueGreen:
      activeService: my-service-active
      previewService: my-service-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 60
```

Create two Services — `my-service-active` (receives production traffic) and `my-service-preview` (receives the new version for validation). The Ingress should point only to `my-service-active`.

When a new image is deployed, ArgoCD Rollouts launches the green pods behind `my-service-preview`, waits for them to pass readiness checks, and then waits for manual promotion approval (because `autoPromotionEnabled: false`). After you validate the preview environment, promote by running `kubectl argo rollouts promote my-service`.

## Validating and Promoting

After the green deployment is up and healthy in preview, validate it before promoting:

1. Check that all green pods show "Ready" in `kubectl get pods -l rollout-id=<rollout>`.
2. Send test traffic to the preview service endpoint and confirm expected behavior.
3. Check key metrics on the monitoring dashboard; compare error rate and latency against the blue baseline.
4. If all checks pass, promote: `kubectl argo rollouts promote my-service`. Traffic switches to green instantly.
5. Monitor for 15 minutes post-promotion. If any metric regresses, abort: `kubectl argo rollouts abort my-service` to immediately return traffic to blue.
