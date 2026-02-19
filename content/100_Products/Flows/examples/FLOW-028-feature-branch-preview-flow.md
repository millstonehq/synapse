---
id: FLOW-028
type: flow
title: Feature Branch Preview Flow
status: deprecated
owner: QA Lead
created: '2025-05-04T12:31:28.308Z'
updated: '2026-09-07T12:26:41.197Z'
tags:
  - flow
  - ci-cd-platform
summary: Feature Branch Preview Flow
feature_area: CI/CD Platform
related_prds:
  - PRD-031
example: true
---

## Steps

### Step 1: PR Creation and Environment Provisioning

A developer opens a pull request against `main`. The GitHub Actions `preview.yml` workflow is triggered by the `pull_request` event with action `opened`. The Preview Environment Generator receives the webhook, checks that the concurrent environment quota is not exceeded (maximum 50 active environments), creates a dedicated Kubernetes namespace named `preview-pr-{number}-{service}`, and applies a Kustomize overlay that points to the PR's container image tag. If the quota limit is reached, the oldest environment is terminated and a Slack notification is sent to its PR author before creating the new one.

### Step 2: Service Deployment to Preview Namespace

The Kustomize overlay deploys the PR's service container image to the preview namespace with resource limits (2 CPU, 2 GB RAM). A Kubernetes Service and Ingress resource are created, routing traffic from a unique URL (`pr-{number}.{service}.preview.internal.example.com`) to the deployed pods. The service connects to in-cluster test fixtures (not staging or production databases) using synthetic connection strings injected as Kubernetes Secrets. The deployment waits for the pod readiness probe to succeed before the environment is marked as ready.

### Step 3: URL Notification

Once the preview environment is ready, the Preview Environment Generator posts a GitHub Check Run comment on the PR with the environment URL and a status badge. The comment includes: the URL, the commit SHA deployed, and a note that the environment will be torn down on PR merge or close. If provisioning fails (e.g., image build failed, quota exceeded after retry), the Check Run is updated with a failure status and an error description. Engineers can trigger a re-provision by pushing a new commit or manually re-running the workflow.

### Step 4: Teardown on PR Close

When the PR is merged or closed, GitHub emits a `pull_request` event with action `closed`. The preview workflow tears down the Kubernetes namespace, Ingress resource, and associated Secrets. The teardown is idempotent; if the namespace was already removed (e.g., quota-driven termination), the teardown step exits cleanly. A final GitHub Check Run update marks the environment as "Terminated" so the PR timeline shows the full lifecycle.

## Expected Results

- Preview environment URL is available within 5 minutes of PR open
- Each open PR has a unique, isolated environment accessible via VPN without any manual setup
- Concurrent environment count stays within the configured quota limit
- Environment teardown is complete within 10 minutes of PR merge or close
- No cross-environment interference: each namespace has separate in-cluster test fixtures and network policies blocking access to other namespaces

## User Info

| Field | Value |
|-------|-------|
| Role | Developer (PR author) and reviewer/QA engineer (environment consumer) |
| Permissions | Read access to preview URLs; no deployment permissions required |
| Environment | `preview` Kubernetes namespace, VPN-only access |
| Trigger | Pull request opened, synchronized (new commit), or closed |
| Lifecycle | Created on PR open; updated on commit push; terminated on PR merge/close |
