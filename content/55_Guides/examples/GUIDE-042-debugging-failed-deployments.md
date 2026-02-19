---
id: GUIDE-042
type: guide
title: Debugging Failed Deployments
status: approved
owner: Developer Experience
created: '2025-12-02T01:11:48.352Z'
updated: '2026-02-17T18:36:34.763Z'
tags:
  - guide
  - ci-cd-platform
summary: Debugging Failed Deployments
audience: customer
related_systems:
  - SYSTEM-032
example: true
---

## Before You Debug: Check the Basics

Most deployment failures fall into a small number of categories. Before diving deep, work through this quick checklist:

- **Is CI passing?** A deployment cannot proceed with a failing CI run. Check the status check on the merged PR — all stages (lint, test, build, security-scan, publish) must be green.
- **Does the image exist in the registry?** Navigate to the container registry and confirm the image tagged with the expected commit SHA is present. A missing image means the publish stage failed or was skipped.
- **Is the GitOps manifest updated?** Open the GitOps repository and verify the image tag in the deployment manifest matches the intended commit SHA. If the manifest is not updated, ArgoCD has nothing new to deploy.
- **Is ArgoCD showing the application as "Synced"?** An OutOfSync state means ArgoCD has seen the manifest change but has not yet applied it, or a sync error is preventing application.

## Reading Kubernetes Pod Failures

If the deployment reaches Kubernetes but pods are not starting, use these commands to diagnose:

```bash
# See pod status and restart counts
kubectl get pods -n <namespace> -l app=<service-name>

# Get detailed events for a stuck or crashlooping pod
kubectl describe pod -n <namespace> <pod-name>

# Read the current container logs
kubectl logs -n <namespace> <pod-name>

# Read logs from the previous (crashed) container instance
kubectl logs -n <namespace> <pod-name> --previous
```

The most common pod failure modes and their causes:

- **CrashLoopBackOff**: The application is starting but crashing on startup. Check the logs from `--previous` for the startup error (missing environment variable, failed database connection, invalid configuration).
- **ImagePullBackOff / ErrImagePull**: The image cannot be pulled. Verify the image tag exists in the registry, check that the image pull secret is valid and attached to the service account, and confirm registry network connectivity.
- **Pending**: The pod cannot be scheduled. Check node resource availability (`kubectl describe nodes`) and verify node selectors or affinity rules match available nodes.
- **OOMKilled**: The container exceeded its memory limit. Either increase the memory limit in the manifest or investigate a memory leak in the application.

## Interpreting ArgoCD Sync Errors

Common ArgoCD sync errors and what to do:

- **"admission webhook denied"**: A cluster policy (PodSecurity, OPA, Kyverno) is rejecting the resource. Read the webhook message in the ArgoCD sync error — it usually tells you exactly which policy failed and why.
- **"field is immutable"**: You are trying to change a field on a resource (like a Deployment's label selector) that cannot be changed in-place. Delete the resource and let ArgoCD re-create it.
- **"resource already exists"**: Another controller or a manual apply created the resource outside of ArgoCD's management. Use `argocd app sync --force` or annotate the resource for ArgoCD adoption.

## When to Roll Back

If debugging takes more than 10 minutes and the service is degraded in production, roll back first and investigate second. A quick rollback to the last known good version restores service for customers while you investigate the failure in a lower-stakes environment. The deployment record captures the previous stable SHA — use it without hesitation.
