---
id: REFERENCE-014
type: reference
title: GitHub Actions Workflow Syntax Reference
status: draft
owner: Platform Team
created: '2024-07-19T01:50:38.113Z'
updated: '2025-09-14T22:07:28.783Z'
tags:
  - reference
  - ci-cd-platform
summary: GitHub Actions Workflow Syntax Reference
upstream_url: https://docs.example.com/github-actions-workflow-syntax-reference
last_synced: '2025-05-05T00:12:52.576Z'
attribution: OWASP Foundation
license: CC BY-SA 4.0
category: specification
example: true
---

## Overview

GitHub Actions workflows are YAML files stored in `.github/workflows/` in a repository. Each workflow file defines one or more jobs that run in response to events (push, pull_request, workflow_dispatch, schedule, etc.). This reference documents the key syntax elements and platform conventions for writing workflows that integrate with the CI/CD platform's standard toolchain.

All platform-provided reusable workflows are maintained in `platform/ci-workflows`. Service teams should use these reusable workflows rather than writing equivalent logic inline. This reference documents both the upstream syntax and the platform's conventions for using it.

## Top-Level Keys

- `name`: Human-readable workflow name displayed in the GitHub Actions UI. Required. Use the format: `{Service Name} CI` or `{Service Name} Deploy`.
- `on`: Defines the triggering events. Standard platform triggers: `push` (for CI on main), `pull_request` (for CI on PRs), `workflow_dispatch` (for manual triggers with input parameters).
- `env`: Workflow-level environment variables available to all jobs. Use for non-secret configuration like registry URLs. Secrets must use `${{ secrets.NAME }}` syntax, not `env`.
- `jobs`: Map of job definitions. Jobs run in parallel by default; use `needs:` for sequential dependencies.

## Job Syntax

Each job entry under `jobs` supports these commonly-used keys:

- `runs-on`: Runner label. Use `self-hosted` with a `platform: ci-runners` label selector for internal network access; use `ubuntu-22.04` for public-only workloads.
- `steps`: Ordered list of step definitions. Steps run sequentially within a job.
- `needs`: List of job IDs this job depends on. Creates a sequential dependency; this job runs only after the listed jobs complete.
- `if`: Conditional expression. Use `github.ref == 'refs/heads/main'` to run only on main branch pushes.
- `permissions`: Restrict the job's GITHUB_TOKEN permissions to the minimum required. Standard build jobs use `contents: read, packages: write`.

## Step Syntax

| Key | Purpose |
|-----|---------|
| `uses` | Reference a reusable action or workflow (e.g., `actions/checkout@v4` or `platform/ci-workflows/.github/actions/docker-build@main`) |
| `run` | Shell command(s) to execute. Multi-line commands use `\|` YAML block scalar |
| `with` | Input parameters for an `uses` action |
| `env` | Step-level environment variables, overriding job-level `env` for this step only |
| `id` | Identifier for this step; used to reference outputs in later steps via `${{ steps.{id}.outputs.{key} }}` |

## Platform Conventions

- All Docker image builds must use the `platform/ci-workflows/.github/actions/docker-build` composite action, which handles Build Cache Service integration and image signing automatically.
- Secret scanning (truffleHog) must be included in all CI workflows as a required step before the build step, using the `platform/ci-workflows/.github/actions/secret-scan` action.
- The `HARBOR_TOKEN` secret is provisioned automatically by the platform team for all repositories; do not create custom registry credentials.
- Workflow files must include `permissions: {}` at the top level with explicit grants per job; wildcard permissions (`permissions: write-all`) are blocked by the CI governance policy.

## Sync Notes

This reference covers GitHub Actions workflow syntax as of 2024. Platform composite actions are versioned via Git tags. Update the `@main` references to a pinned tag for production workflows to ensure stability across platform action updates.
