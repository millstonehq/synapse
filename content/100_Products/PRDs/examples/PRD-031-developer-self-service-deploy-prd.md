---
id: PRD-031
type: prd
title: Developer Self-Service Deploy PRD
status: accepted
owner: Head of Product
created: '2024-07-10T07:51:08.617Z'
updated: '2026-11-07T05:00:11.357Z'
tags:
  - prd
  - ci-cd-platform
summary: Developer Self-Service Deploy PRD
related_tdds:
  - TDD-035
  - TDD-032
example: true
related_standards:
  - STANDARD-040
---

## Summary

Provide developers with a self-service interface to trigger, monitor, and roll back production deployments for their own services without requiring on-call engineer or platform team intervention. Currently, all production deployments must be coordinated through the platform team's deployment rotation, creating a bottleneck that contributes to a median lead time of 4.8 days and causes developer frustration. This product gives service owners direct, governed access to deploy their services through a UI and CLI, backed by the existing Deployment Controller and ArgoCD infrastructure.

## Goals

- Reduce median lead time for changes from 4.8 days to under 24 hours by eliminating the deployment coordination bottleneck
- Enable service owners to deploy, verify, and roll back their services without platform team involvement
- Maintain existing governance controls (approval gates, canary analysis, deployment windows) as part of the self-service flow
- Provide real-time deployment status visibility to deploying engineers without requiring ArgoCD console access

## In Scope

- Web UI for initiating a deployment from an approved artifact version
- CLI command (`plat deploy`) for CI and terminal-based workflows
- Real-time deployment status stream (pod rollout progress, health check results, canary analysis status)
- One-click rollback to any of the last 10 deployed versions
- Deployment history view per service with commit, deployer, timestamp, and outcome
- Integration with the existing approval workflow for services requiring gate sign-off

## Out of Scope

- Multi-service orchestrated deployments (e.g., deploy service A then B in sequence)
- Environment creation or teardown (handled by separate infrastructure tools)
- Infrastructure changes (Terraform, Kubernetes node pools)
- Non-Kubernetes deployment targets

## Users and Flows

**Service owners (primary users)** are engineers who own one or more production services. They use the self-service deploy interface most often at the conclusion of a feature cycle: they select the artifact version they want to promote, confirm the approval gate is satisfied, trigger the deployment, and monitor the rollout from the status page. If metrics degrade during the monitoring window, they click Rollback.

**Platform team engineers** use the same interface for all deployments, replacing their current workflow of logging into ArgoCD directly. The self-service UI becomes the standard deployment interface for all engineers. Platform engineers retain admin access to ArgoCD for debugging and emergency operations not covered by the UI.

**On-call engineers** use the rollback capability during incident response without needing to know ArgoCD syntax. A single click from the deployment history page triggers the rollback and streams the status back to the engineer, replacing a multi-step CLI process.

## Requirements

- Display available artifact versions for a service, sourced from Harbor registry with build metadata (commit SHA, CI run link, build timestamp)
- Trigger deployment via the Deployment Controller API with the selected artifact version and any required approval token
- Stream pod rollout status updates in real time via server-sent events (SSE) without requiring page refresh
- Surface the canary analysis result (pass/fail/in-progress) during canary deployment phases
- Initiate rollback to a selected previous version with a confirmation dialog
- Record all deployment actions in an immutable audit log accessible from the deployment history view
- CLI (`plat deploy --service {name} --version {sha}`) produces the same behavior as the web UI with streaming output to stdout
- Enforce deployment window restrictions (no production deploys outside allowed windows for restricted services)

## KPIs

- **Median lead time for changes**: Target < 24 hours (from merge to production), down from 4.8 days
- **Self-service deployment rate**: > 90% of production deployments initiated without platform team coordination within 3 months of launch
- **Mean time to rollback**: Target < 3 minutes from decision to rollback complete
- **Developer satisfaction (NPS)**: Measured via quarterly survey; target improvement of 15+ points for deployment experience

## Information Architecture

- Self-service deploy UI documentation lives in `55_Guides/` (user-facing how-to)
- Technical design in `90_Architecture/TDDs/` (see [[TDD-035|TDD-035]] and [[TDD-032|TDD-032]])
- Deployment standards in `20_Standards/` governing window restrictions and approval requirements
- This PRD in `100_Products/PRDs/` defining requirements

## Data Model

- **DeploymentRequest**: `id`, `service_name`, `artifact_version`, `initiator`, `approval_token`, `status`, `created_at`, `completed_at`
- **DeploymentEvent**: Immutable log of each status transition and health check result during a deployment
- **ArtifactVersion**: Projection from Harbor registry: `digest`, `commit_sha`, `pushed_at`, `ci_run_url`, `vulnerability_status`
- **RollbackTarget**: Reference to a previous `DeploymentRequest` that represents a known-good deployment; used when initiating rollback

## Non-Functional

- Deployment status stream must deliver updates within 2 seconds of the underlying Kubernetes event
- Web UI must render the deployment status page within 1 second on a 25 Mbps connection
- All deployment actions must be persisted in the audit log before the action is submitted to the Deployment Controller
- CLI must work without browser; must support non-interactive mode for use in scripts (`--no-confirm` flag)
- No storage of credentials or tokens beyond the session; authentication via SSO/OIDC with the existing identity provider

## Constraints

- Must use the existing Deployment Controller API; no direct ArgoCD API calls from the UI
- Must not bypass approval gates; approval token must be validated before deployment is submitted
- Must integrate with the existing SSO identity provider for authentication; no local user accounts
- Rollback must use the same promotion pipeline as forward deployment; no direct image tag manipulation

## Risks

- **Governance regression risk**: Self-service access could lead to engineers bypassing approval requirements. Mitigation: approval gate validation is enforced in the Deployment Controller, not the UI; the UI cannot submit a deployment without a valid token.
- **Scope creep to infrastructure changes** if users request self-service Terraform or node pool changes. Mitigation: explicitly out of scope; separate product initiative required.
- **Adoption plateau** if CLI tooling is not ergonomic for terminal-focused engineers. Mitigation: CLI is a first-class deliverable; usability testing with 5 engineers before launch.

## Milestones

### M1: Web UI and Artifact Selection (Weeks 1-3)

#### Deliverables

- Deployment initiation page with artifact version picker sourced from Harbor
- Deployment status page with real-time SSE stream
- Audit log recording all initiated deployments

#### Acceptance Criteria

- Engineer can select an artifact version and trigger a deployment from the web UI
- Status page reflects pod rollout progress within 3 seconds of each Kubernetes event
- All initiated deployments appear in audit log within 1 second

### M2: Rollback and History (Weeks 4-5)

#### Deliverables

- Deployment history page per service showing last 50 deployments
- One-click rollback to any listed deployment with confirmation dialog
- CLI (`plat deploy`) with equivalent functionality to the web UI

#### Acceptance Criteria

- Rollback can be triggered from the history page and completes within 5 minutes for a standard service
- CLI produces streaming status output equivalent to the web UI
- History page loads within 1 second for a service with 50 deployments
