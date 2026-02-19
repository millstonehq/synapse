---
id: SOP-064
type: sop
title: Clear Build Cache SOP
status: approved
owner: DevOps Lead
created: '2025-09-10T00:25:54.429Z'
updated: '2025-04-18T20:44:50.540Z'
tags:
  - sop
  - ci-cd-platform
summary: Clear Build Cache SOP
related_process: PROCESS-039
related_systems:
  - SYSTEM-034
example: true
---

## Preconditions

- You have identified a caching issue: builds are failing with stale dependency errors, unexpected test failures on a clean branch, or builds succeeding locally but failing in CI
- You have confirmed the failure is not caused by a code or configuration change (rule out legitimate failures first)
- You have write access to the repository and access to the CI platform's cache management interface

## Materials/Access

- Access to the CI platform UI with cache management capability (GitHub Actions cache API, GitLab CI cache settings, or equivalent)
- Write access to the affected repository (to push a cache-busting commit if needed)
- Access to #ci-support Slack channel if escalation is needed
- The name of the cache key prefix or cache key pattern for the affected pipeline

## Procedure

1. Identify the specific cache key causing the problem by inspecting the pipeline logs for cache hit/miss messages and noting the exact cache key string.
2. Open the CI platform's cache management interface (GitHub Actions: Settings → Caches, GitLab CI: CI/CD → Pipelines → Caches) and search for the cache key.
3. Select the stale cache entry or entries matching the affected repository and branch, and delete them using the platform's cache deletion UI.
4. If the CI platform does not provide a UI for cache deletion, modify the cache key in the pipeline configuration file by appending a cache-busting suffix (e.g., change `cache-key-v1` to `cache-key-v2`) and commit the change.
5. Re-trigger the failing pipeline (either by pushing an empty commit or using the "Re-run" button); the build should now perform a full cache miss and rebuild from scratch.
6. Monitor the pipeline run to ensure the build succeeds and the new cache is populated without errors.
7. If the cache-busting was done via pipeline configuration change, verify the suffix increment is preserved going forward; revert only if a permanent change is not appropriate.
8. Document the cache issue and resolution in the PR or team Slack channel for future reference.

## Validation

- The pipeline run after cache clearing completes successfully with a cache miss (visible in logs as "Cache not found" followed by successful dependency install)
- Subsequent runs show a cache hit and complete in reduced time, confirming the new cache was populated correctly
- The original failure does not recur on the same branch

## Rollback

1. If clearing the cache causes builds to fail due to an unrelated dependency resolution problem (e.g., a dependency version no longer available upstream), restore the previous cache key suffix in the pipeline configuration.
2. If a dependency resolution failure is exposed by the cache clear, pin the failing dependency to the last known good version in the manifest file before re-running.
3. If cache clearing does not resolve the original failure, escalate to the platform team as the issue may be in runner disk state rather than cached artifacts.
