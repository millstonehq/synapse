---
id: FLOW-025
type: flow
title: Continuous Integration Pipeline Flow
status: review
owner: QA Engineer
created: '2025-07-26T15:52:25.002Z'
updated: '2025-01-01T13:23:36.113Z'
tags:
  - flow
  - ci-cd-platform
summary: Continuous Integration Pipeline Flow
feature_area: CI/CD Platform
related_prds:
  - PRD-032
example: true
---

## Steps

### Step 1: Code Push and Trigger

A developer pushes a commit to a feature branch or merges a pull request to `main`. GitHub emits a `push` or `pull_request` event that triggers the CI workflow in GitHub Actions. The workflow begins with a checkout step to clone the repository at the pushed commit SHA. A cache restore step attempts to load the Go module cache and the Docker layer cache from the Build Cache Service, keyed by the dependency lockfile hash.

### Step 2: Build and Lint

The workflow runs linting (golangci-lint for Go services, eslint for Node services) and compiles the service binary or builds the Docker image. If the linter or build step fails, the workflow exits and the PR is blocked; no further steps run. Secret scanning (truffleHog) runs in parallel with linting to detect accidentally committed credentials before the code proceeds to testing.

### Step 3: Test Execution

Unit tests run in parallel across the test suite using GitHub Actions matrix strategy. Integration tests run against a local Docker Compose stack spun up by the test runner. Test results are published to the GitHub Checks API as individual annotations. If any test suite fails, the workflow marks the CI run as failed and posts the failure summary to the PR as a review comment.

### Step 4: Artifact Build and Push

On a successful test run, the Docker image is built using the multi-stage Dockerfile with layer caching provided by the Build Cache Service. The image is tagged with the commit SHA and pushed to Harbor's `dev` project repository. The image digest is written to a workflow output for use by downstream promotion steps. A Cosign signature is applied to the image digest using the platform signing key stored in Kubernetes secrets.

### Step 5: CI Status Report

The workflow posts the final status to the GitHub Checks API: pass (all steps green), fail (any step failed), or neutral (skipped due to path filter). The Build Orchestration Service receives a webhook with the build outcome, duration, and cache hit/miss metrics for tracking in the Build Performance Dashboard. If the branch is `main` and all steps pass, the workflow triggers the artifact promotion pipeline for the `dev` → `staging` gate.

## Expected Results

- All commits to PRs receive a pass/fail CI status within 8 minutes of push
- Docker images are built and pushed to Harbor for all successful main branch commits
- Secret scanning blocks merges that contain credential patterns before they reach the repository history
- Build cache hit rate above 70% keeps incremental build times under 3 minutes for services with unchanged dependencies
- Lint and test failures appear as inline PR annotations identifying the specific file and line

## User Info

| Field | Value |
|-------|-------|
| Role | CI service account (GitHub Actions runner) |
| Permissions | Read repo, write checks, push to Harbor dev project |
| Test environment | GitHub Actions runner fleet (Kubernetes self-hosted) |
| Trigger | push to any branch, pull_request opened/synchronized |
| Environment | CI (isolated runner namespace) |
