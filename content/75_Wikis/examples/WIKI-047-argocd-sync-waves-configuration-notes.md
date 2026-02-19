---
id: WIKI-047
type: wiki
title: ArgoCD Sync Waves - Configuration Notes
status: approved
owner: CI/CD Team
created: '2025-08-12T14:47:15.501Z'
updated: '2025-11-06T14:11:15.406Z'
tags:
  - wiki
  - ci-cd-platform
summary: ArgoCD Sync Waves - Configuration Notes
source_repo: https://git.example.com/acme/argocd-sync-waves
commit_sha: 8386368a8f53e0628dda131dde83f1e21d88bdb4
generated_at: '2025-06-18T15:35:27.277Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: medium
example: true
---

## Overview

ArgoCD Sync Waves is a feature that controls the order in which resources are applied during a sync operation. By default, ArgoCD applies all resources in an Application simultaneously, which can cause race conditions when some resources depend on others being ready first (e.g., a Deployment that depends on a ConfigMap, or a service that depends on a CRD being registered). Sync waves solve this by grouping resources into ordered batches and waiting for each wave to reach a healthy state before proceeding to the next.

Sync waves are specified via the annotation `argocd.argoproj.io/sync-wave: "{N}"` where `N` is an integer. Resources with lower wave numbers are applied first. Resources without this annotation are assigned wave 0 by default.

## How Waves Work

ArgoCD processes waves in ascending order. Within a wave, all resources are applied simultaneously. ArgoCD waits for all resources in a wave to report as `Healthy` (or at minimum `Synced`, for resources without a health check) before beginning the next wave. If any resource in a wave fails to become healthy within the configured timeout (default: 5 minutes), the sync is halted and the Application enters a `Degraded` state.

The wave execution model:

- Wave -5: Namespaces, CRDs (must exist before any resources that use them)
- Wave -1: ConfigMaps, Secrets (configuration that pods read at startup)
- Wave 0: Services, ServiceAccounts, RBAC (default wave; most resources land here)
- Wave 1: Deployments, StatefulSets (application workloads that depend on wave 0)
- Wave 5: Ingress, HPA (routing and scaling rules applied after pods are running)

## Key Components

- **Namespace and CRD resources** use wave `-5` to ensure they are registered before any workloads that reference them. Deploying a CRD in the same wave as a resource that uses it will cause a sync failure because the CRD controller may not be ready.
- **Database migration jobs** should be placed in a wave lower than the application Deployment that depends on the migrated schema. A common pattern is migration Job in wave `0` with the Deployment in wave `1`; ArgoCD waits for the Job to complete successfully before proceeding.
- **Readiness-gating with hooks**: For more complex dependencies (e.g., wait for an external API to be available), ArgoCD sync hooks (`argocd.argoproj.io/hook: PreSync`) provide an alternative to waves. Hooks execute before the sync begins and can block the sync if they fail.

## Configuration

| Annotation | Example Value | Effect |
|------------|---------------|--------|
| `argocd.argoproj.io/sync-wave` | `"-5"`, `"0"`, `"1"`, `"5"` | Assigns the resource to the specified wave |
| `argocd.argoproj.io/hook` | `"PreSync"`, `"PostSync"` | Runs a Job before or after the sync instead of as a wave resource |
| `argocd.argoproj.io/hook-delete-policy` | `"HookSucceeded"` | Deletes the hook Job after successful completion |

## Dependencies

Sync wave ordering has a dependency relationship with the following platform components:

- **ArgoCD Application CRD**: The `syncPolicy` field controls whether sync is automated; waves apply equally to manual and automated syncs
- **ArgoCD Rollouts**: When using ArgoCD Rollouts for canary deployments, the Rollout resource itself should be placed in the same wave as a standard Deployment; Rollout-managed Pods are managed by the Rollout controller, not ArgoCD directly
- **Kustomize overlays**: Wave annotations can be added via Kustomize patches in environment-specific overlays, allowing different wave assignments for the same resource across staging and production without modifying the base manifest
