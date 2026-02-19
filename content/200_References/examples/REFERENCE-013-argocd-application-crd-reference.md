---
id: REFERENCE-013
type: reference
title: ArgoCD Application CRD Reference
status: draft
owner: Security Team
created: '2025-04-23T11:54:28.345Z'
updated: '2026-08-30T16:36:54.290Z'
tags:
  - reference
  - ci-cd-platform
summary: ArgoCD Application CRD Reference
upstream_url: https://docs.example.com/argocd-application-crd-reference
last_synced: '2026-12-18T16:18:41.742Z'
attribution: NIST
license: CC BY-SA 4.0
category: documentation
example: true
---

## Overview

The ArgoCD Application CRD (Custom Resource Definition) defines a declarative deployment target that ArgoCD continuously reconciles. An Application resource specifies the desired state (source Git repository, path, and revision) and the target Kubernetes cluster and namespace. ArgoCD monitors both the source repository and the live cluster state and applies changes when they diverge.

This reference documents the core Application spec fields as used in our platform. For the complete upstream CRD specification, see the upstream URL. All platform-managed Applications are generated from ApplicationSet templates; direct Application creation is restricted to the platform team.

## Core Spec Fields

### `spec.source`

Defines where ArgoCD reads the desired state from.

- `repoURL`: The Git repository URL. All platform repositories are in `https://git.example.com/platform/k8s-manifests`.
- `targetRevision`: The Git branch, tag, or commit SHA to track. Production Applications use `HEAD` (tracks main branch); staging Applications may pin to a specific tag.
- `path`: The directory within the repository containing the Kubernetes manifests or Helm chart. Convention: `services/{service-name}/{environment}/`.
- `helm` or `kustomize`: Optional configuration for Helm chart overrides or Kustomize overlay parameters.

### `spec.destination`

Defines where ArgoCD deploys the manifests.

- `server`: The Kubernetes API server URL. Use `https://kubernetes.default.svc` for in-cluster Applications.
- `namespace`: The target Kubernetes namespace. Production Applications use the service's production namespace; staging uses the staging namespace.

### `spec.syncPolicy`

Controls how and when ArgoCD syncs.

- `automated.prune: true` — ArgoCD deletes resources that are in the cluster but no longer in the Git source. Required for all platform Applications.
- `automated.selfHeal: true` — ArgoCD reverts out-of-band changes within the sync interval (default: 3 minutes). Prevents configuration drift.
- `syncOptions` — Commonly used: `CreateNamespace=true` (create namespace if absent), `ServerSideApply=true` (use server-side apply for large resources).

## ApplicationSet Usage

Platform Applications are not created directly. Instead, an ApplicationSet in the `argocd` namespace generates Application resources from a template. The generator uses a Git file generator to discover service directories. Each directory containing an `app.yaml` descriptor file produces one Application per environment. This pattern ensures all Applications share consistent sync policies and naming conventions without manual Application management.

## Common Annotations

| Annotation | Purpose |
|------------|---------|
| `argocd.argoproj.io/sync-wave` | Controls sync order when multiple Applications must sync in sequence |
| `notifications.argoproj.io/subscribe.on-sync-failed.slack` | Slack channel to notify on sync failure |
| `argocd.argoproj.io/managed-by` | Set to `argocd` to indicate platform management; prevents accidental deletion |

## Sync Notes

This reference covers ArgoCD Application CRD fields as used with ArgoCD v2.10. Field availability may differ for older or newer versions. Re-sync this document when upgrading ArgoCD to a new minor version.
