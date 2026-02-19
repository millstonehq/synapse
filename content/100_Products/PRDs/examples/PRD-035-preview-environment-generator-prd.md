---
id: PRD-035
type: prd
title: Preview Environment Generator PRD
status: review
owner: Head of Product
created: '2025-08-10T20:44:50.825Z'
updated: '2026-07-08T00:42:59.040Z'
tags:
  - prd
  - ci-cd-platform
summary: Preview Environment Generator PRD
related_tdds:
  - TDD-033
  - TDD-031
example: true
related_standards:
  - STANDARD-040
---

## Summary

Automatically provision ephemeral preview environments for every open pull request, allowing developers and QA engineers to test feature branches against a production-like environment without manual setup. Currently, testing feature branches requires manually coordinating a shared staging environment, which causes conflicts when multiple teams need the environment simultaneously and delays code review feedback cycles. Preview environments will be created automatically when a PR is opened and torn down when the PR is merged or closed.

## Goals

- Eliminate staging environment conflicts by giving each open PR its own isolated environment
- Reduce PR-to-review cycle time by making it easy for reviewers to test changes without local setup
- Support QA engineers in testing feature branches before merge approval
- Automatically clean up resources to avoid unbounded infrastructure cost growth

## In Scope

- Automatic environment creation on PR open or first commit push
- Deployment of the PR's service build to a dedicated Kubernetes namespace
- Unique URL per environment, publicly accessible within the corporate VPN
- Environment teardown on PR merge or close
- Environment URL posted as a GitHub PR comment within 5 minutes of PR creation
- Cost cap: maximum 50 active preview environments at any time; oldest environments are terminated when the limit is reached

## Out of Scope

- Multi-service preview environments (only the changed service is deployed; dependencies use staging mocks or shared staging services)
- Database migrations in preview environments (preview environments use a sanitized snapshot of staging data)
- Load testing or performance testing in preview environments
- Preview environments for non-Kubernetes services

## Users and Flows

**Developers** open a PR and within 5 minutes see a PR comment with a link to the preview environment for their service. They can click the link to verify the behavior of their change end-to-end before requesting review. If they push another commit, the environment is updated automatically.

**Reviewers and QA engineers** click the preview environment link in the PR to test the feature branch changes without needing to check out the branch locally. For UI changes, they can visually verify the behavior. For API changes, they use the environment URL as a base URL for ad-hoc testing with curl or Postman.

**Engineering managers** use the preview environment system to enable async review workflows: reviewers in different time zones can test feature branches independently without coordinating access to a shared environment.

## Requirements

- Create a Kubernetes namespace per PR with a unique name derived from the PR number and service name
- Deploy the PR's container image (built by CI) to the preview namespace via ArgoCD or Kustomize overlay
- Provision an ingress rule with a unique URL pattern (e.g., `pr-{number}.{service}.preview.internal.example.com`)
- Post the environment URL as a GitHub PR comment using the GitHub Checks API
- Update the deployment when new commits are pushed to the PR branch
- Tear down the namespace and ingress on PR merge or close
- Enforce a maximum of 50 concurrent preview environments; oldest-by-creation terminated when limit is reached
- Send a Slack message to the PR author's channel when their environment is terminated due to the limit

## KPIs

- **Environment provisioning time**: Target < 5 minutes from PR open to environment available
- **Concurrent environments supported**: At least 50 active preview environments without degrading the preview cluster
- **Cost per environment-day**: Target < $2/environment/day (compute + storage)
- **Developer adoption**: > 60% of open PRs have at least one preview environment access event within 30 days of launch

## Information Architecture

- Technical design in `90_Architecture/TDDs/` (see [[TDD-033|TDD-033]])
- Preview environment architecture notes in `75_Wikis/`
- This PRD in `100_Products/PRDs/`

## Data Model

- **PreviewEnvironment**: `id`, `pr_number`, `service_name`, `namespace`, `url`, `image_tag`, `status` (Provisioning/Active/Terminating/Terminated), `created_at`, `terminated_at`
- **PreviewEvent**: Immutable log of lifecycle events: `environment_id`, `event_type` (Created/Updated/Terminated/LimitTerminated), `triggered_by`, `occurred_at`
- **EnvironmentQuota**: Singleton config: `max_active_environments`, `current_active_count` — enforced at creation time

## Non-Functional

- Each preview environment must be isolated at the Kubernetes namespace level; cross-namespace network access is blocked by NetworkPolicy
- Preview environments must not share secrets with production; all secrets are synthetic test values
- Compute resources per preview environment must be capped (2 CPU / 2 GB RAM) to prevent runaway cost
- Preview environment URLs are accessible only within the corporate VPN

## Constraints

- Must use existing Kubernetes cluster with a dedicated `preview` node pool; no new cloud accounts
- Only the service being PR'd is deployed; no automatic deployment of service dependencies
- Cannot access production databases; must use a sanitized staging data snapshot
- Preview environments for services requiring special infrastructure (GPU, external hardware integrations) are not supported

## Risks

- **Preview cluster capacity exhaustion** if 50 environments all provision simultaneously after a company-wide push. Mitigation: implement a queue with a maximum creation rate of 5 environments per minute.
- **Data isolation failure** if a preview environment accidentally connects to a staging or production database. Mitigation: preview namespaces have no route to database subnets; all database connections use in-cluster test fixtures.
- **Preview environment URL confusion** if engineers bookmark a URL that later resolves to a different PR's environment. Mitigation: include PR number in the URL pattern; document that URLs are ephemeral in the PR comment.

## Milestones

### M1: Environment Provisioning (Weeks 1-3)

#### Deliverables

- Kubernetes namespace provisioner triggered by GitHub PR webhook
- ArgoCD Application or Kustomize overlay deploying the PR image to the preview namespace
- Ingress rule creation with unique URL

#### Acceptance Criteria

- Preview environment for a test service is provisioned within 5 minutes of PR creation
- Environment is accessible via the assigned URL from the corporate VPN

### M2: Lifecycle Management and GitHub Integration (Weeks 4-5)

#### Deliverables

- GitHub PR comment with environment URL posted on provisioning completion
- Environment update on new commit push
- Namespace teardown on PR merge or close
- Maximum concurrent environment quota enforcement

#### Acceptance Criteria

- PR comment appears within 5 minutes of PR open
- Namespace is fully deleted within 10 minutes of PR merge
- When 50th environment is active, 51st PR triggers termination of oldest environment with Slack notification
