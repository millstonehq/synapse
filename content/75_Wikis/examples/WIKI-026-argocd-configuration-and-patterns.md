---
id: WIKI-026
type: wiki
title: ArgoCD - Configuration and Patterns
status: approved
owner: CI/CD Team
created: '2025-01-24T05:16:12.484Z'
updated: '2026-05-04T14:54:22.263Z'
tags:
  - wiki
  - ci-cd-platform
summary: ArgoCD - Configuration and Patterns
source_repo: https://git.example.com/acme/argocd
commit_sha: 1405561bbef0d97c74c948f3fc068efe91c7c0f0
generated_at: '2025-07-23T23:30:54.095Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: medium
example: true
---

## Overview

ArgoCD is the GitOps continuous delivery tool used by the CI/CD platform to manage Kubernetes deployments. All production and staging deployments are driven by ArgoCD Application and ApplicationSet resources stored in the `gitops-config` repository. The Deployment Controller issues ArgoCD sync calls; ArgoCD executes them and reports health status back.

This wiki documents the conventions, patterns, and gotchas observed in operating ArgoCD at scale across 40+ services and 3 environments.

## Architecture

ArgoCD runs as a set of controllers in the `argocd` namespace on the platform cluster. Key components:

- **Application Controller**: Watches Application CRDs, computes the diff between desired (Git) and live (cluster) state, and executes syncs
- **Repo Server**: Clones and renders manifests (Helm, Kustomize, or plain YAML) from the `gitops-config` repository
- **API Server**: Provides the REST/gRPC API consumed by the ArgoCD UI, CLI, and the Deployment Controller

All service manifests are organized under `gitops-config/apps/{env}/{service}/`. ApplicationSets dynamically generate Application resources from directory structure, eliminating per-service boilerplate.

## Key Components

### ApplicationSet Pattern

Services are onboarded by adding a directory to `gitops-config/apps/`. The platform-wide ApplicationSet picks up new directories automatically:

```yaml
generators:
  - git:
      repoURL: https://git.example.com/acme/gitops-config
      revision: HEAD
      directories:
        - path: apps/*/*
```

### Sync Policies

- **Staging**: Auto-sync enabled. Changes merged to `main` in a service repo trigger CI, which updates the image tag in `gitops-config` and ArgoCD syncs automatically.
- **Production**: Auto-sync disabled. The Deployment Controller calls `argocd app sync` explicitly after approval gates pass.

### Health Checks

All services must expose a `/healthz` endpoint returning HTTP 200. ArgoCD uses this to determine `Healthy` vs `Degraded` post-sync. The Deployment Controller polls ArgoCD health status every 30 seconds after issuing a sync.

## Configuration

Key ArgoCD settings in use:

| Setting | Value | Notes |
|---------|-------|-------|
| `server.insecure` | false | TLS enforced |
| `application.resourceTrackingMethod` | `annotation` | Avoids label conflicts |
| `controller.selfHealInterval` | `5m` | Self-heal checks every 5 minutes |
| `repoServer.parallelismLimit` | `10` | Max concurrent renders |

## Dependencies

- `gitops-config` repository — source of truth for all manifest state
- Deployment Controller — issues sync calls and polls health
- Kubernetes cluster — target for all managed workloads
- OIDC provider — ArgoCD SSO for UI and CLI access
