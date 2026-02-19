---
id: ADR-0026
type: adr
title: Adopt ArgoCD for GitOps Deployments
status: approved
owner: Staff Engineer
created: '2025-02-22T04:40:33.184Z'
updated: '2026-12-08T20:38:58.767Z'
tags:
  - adr
  - ci-cd-platform
summary: Adopt ArgoCD for GitOps Deployments
example: true
supersedes: ADR-0029
---

## Context

The platform engineering team needed a GitOps-based deployment system for all production services running on Kubernetes. Prior to this decision, deployments were executed manually by engineers running `kubectl apply` or `helm upgrade` commands against production clusters from local machines. This approach had several critical problems: there was no audit trail of who deployed what and when, deployment state could drift from what was stored in Git, and there was no automated mechanism to detect or remediate configuration drift.

The team evaluated several tools that implement GitOps principles, requiring a solution that could manage hundreds of Kubernetes resources across multiple namespaces, support canary deployment strategies, integrate with our existing GitHub-hosted manifest repositories, and provide a declarative model where desired state is defined in Git and the controller continuously reconciles actual state toward it.

The organization was already running Flux CD in a limited capacity on one team, and ArgoCD was being trialed informally by the platform team. Evaluating both tools head-to-head with a representative workload was a prerequisite for this decision.

## Decision

Adopt **ArgoCD** as the standard GitOps deployment controller for all Kubernetes-based production services.

Each service will have a dedicated ArgoCD Application resource pointing to a path in its Kubernetes manifest repository. ApplicationSet resources will be used for managing multi-environment (staging, production) Applications from a single template. All Applications will use automated sync with self-healing enabled, meaning ArgoCD will reconcile any out-of-band changes within 3 minutes. Canary rollouts will be implemented using ArgoCD Rollouts, which replaces the standard Deployment resource with a Rollout CRD supporting progressive delivery strategies.

## Consequences

**Positive:**
- Full audit trail of every sync event tied to a Git commit SHA and author
- Configuration drift is detected and auto-remediated within the sync interval
- Canary deployments and automated rollback are supported natively via ArgoCD Rollouts
- Web UI and CLI provide clear visibility into sync status and health across all environments

**Negative:**
- Teams must migrate existing Helm-based deployments to ArgoCD Applications, which requires upfront migration effort
- ApplicationSet and Rollout CRDs add complexity compared to plain Deployments; teams need to learn new concepts
- ArgoCD itself becomes a critical piece of infrastructure requiring its own HA setup and runbook

**Neutral:**
- Both Flux and ArgoCD are CNCF projects with strong community support; the choice is largely operational preference
- Migrating back to Flux or another tool would require re-creating all Application definitions but Git manifests themselves would be unchanged

## Alternatives Considered

**Flux CD:**
- Pro: Lighter weight than ArgoCD, no web UI overhead, pure Git-push model with strong multi-tenancy
- Con: No built-in web UI for deployment visibility (requires additional tooling). Progressive delivery requires separate Flagger installation with more complex integration. Smaller team familiarity with Flux compared to ArgoCD.
- Rejected because: The platform team prioritized a unified UI for deployment status and the ArgoCD Rollouts integration for canary deployments without a separate Flagger deployment.

**Manual `kubectl apply` with CI scripts:**
- Pro: No new infrastructure to operate, maximum control over deployment logic
- Con: No GitOps reconciliation loop means drift is undetected. No audit trail beyond CI logs. Rollback requires manual intervention. Does not scale as service count grows.
- Rejected because: The absence of drift detection and automated reconciliation was identified as an unacceptable operational risk after two production incidents caused by out-of-band changes.

**Spinnaker:**
- Pro: Mature multi-cloud CD platform with advanced pipeline capabilities, Netflix-battle-tested
- Con: Extremely heavyweight infrastructure requirement (multiple microservices, complex setup). Overkill for Kubernetes-only workloads. High operational burden for a small platform team.
- Rejected because: Operational complexity and resource requirements were disproportionate to the team's scale.
