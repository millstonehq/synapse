---
id: SOP-061
type: sop
title: Unblock Failing CI Pipeline SOP
status: approved
owner: Release Manager
created: '2024-11-02T23:28:57.683Z'
updated: '2025-07-09T02:34:26.349Z'
tags:
  - sop
  - ci-cd-platform
summary: Unblock Failing CI Pipeline SOP
related_process: PROCESS-038
related_systems:
  - SYSTEM-032
example: true
---

## Preconditions

- A CI pipeline is failing on a branch that is blocking a pull request merge or a production deployment
- You have identified which stage and job is failing (visible in the pipeline UI or status check on the PR)
- You have developer-level access to the repository and read access to the CI pipeline logs
- No active incident is in progress on the CI platform itself; if the CI platform is down, follow the CI platform outage runbook instead

## Materials/Access

- Access to the CI platform UI (GitHub Actions, GitLab CI, or equivalent) with pipeline log visibility
- Write access to the affected repository to push fixes or retrigger jobs
- Access to the #ci-support Slack channel for escalation if needed
- Access to the secrets manager if the failure is credential-related

## Procedure

1. Open the failing pipeline run in the CI platform UI and navigate to the failing job; read the full error output, scrolling past retry noise to find the root error message.
2. Classify the failure type: transient infrastructure error (network timeout, runner OOM, registry pull failure), flaky test, legitimate test failure, or configuration error.
3. If the failure is a transient infrastructure error (e.g., "connection reset by peer," "context deadline exceeded"), click "Re-run failed jobs" without making any code changes; log the rerun in the PR comment.
4. If the failure is a flaky test with a known issue, re-run the job and open or link to the existing flaky test ticket; do not merge if the test fails again on the rerun.
5. If the failure is a legitimate test or lint failure, stop here and do not attempt to bypass; the code change must be fixed before proceeding.
6. If the failure is a credential or secrets error (e.g., "authentication required," "permission denied to registry"), rotate or refresh the affected credential per the secrets rotation SOP and re-trigger the pipeline.
7. If the failure is a pipeline configuration syntax error, fix the YAML configuration file, push to the branch, and allow the pipeline to re-run automatically.
8. After a successful rerun, post a comment on the PR documenting the failure type, the action taken, and the outcome.

## Validation

- The CI pipeline shows all stages passing (green) on the most recent run for the branch
- The status check on the pull request shows "All checks passed"
- No new failures have appeared in the re-run that were not present before
- The PR comment documents the failure cause and resolution

## Rollback

1. If a configuration fix you pushed breaks additional pipeline stages, revert the configuration commit by running `git revert <commit-sha>` and pushing the revert to the branch.
2. If a credential rotation caused new failures, verify the new credential is correctly stored in the secrets manager and that the pipeline secret reference matches.
3. If re-runs continue to fail without a clear root cause, escalate to the platform team via #ci-support and do not merge the PR.
