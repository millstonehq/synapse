---
id: SOP-065
type: sop
title: Investigate Flaky Test in CI SOP
status: review
owner: Release Manager
created: '2024-08-27T06:17:20.630Z'
updated: '2025-09-01T02:30:16.124Z'
tags:
  - sop
  - ci-cd-platform
summary: Investigate Flaky Test in CI SOP
related_process: PROCESS-037
related_systems:
  - SYSTEM-031
example: true
---

## Preconditions

- A test has been observed failing intermittently (not on every run) in CI across multiple pull requests or branches
- The failing test is not correlated with any code change that could explain the failure
- You have identified the test name, file, and the CI job in which it runs
- You have access to at least 3 pipeline runs showing the failure to establish a pattern

## Materials/Access

- Access to the CI platform UI with pipeline run history for at least the past 7 days
- Ability to run the test locally in a controlled environment
- Read access to the test code and any external dependencies the test may contact
- Access to the flaky test tracking spreadsheet or issue tracker where known flaky tests are catalogued

## Procedure

1. Search the flaky test tracking catalogue to determine whether this test is already documented; if so, link to the existing ticket and skip steps 2-5.
2. Collect at least 5 recent pipeline run logs where the test failed; note the error message, stack trace, and any timestamps or resource metrics visible in the log.
3. Identify the failure pattern: does the failure occur at a specific time of day, on specific runner types, after specific parallel jobs, or only under heavy load? Record observations.
4. Run the test locally 10 times in rapid succession using `go test -count=10 -run TestFlakyName ./...` (or equivalent); note whether the failure reproduces locally.
5. If the test contacts external services (database, HTTP endpoint, file system), examine whether the failure is caused by a race condition, timing dependency, or resource contention by reviewing the test setup and teardown code.
6. Quarantine the flaky test by adding it to the CI skip list with a comment linking to the tracking ticket; this prevents the test from blocking other engineers while the fix is in progress.
7. Create a tracking ticket with the failure pattern evidence, suspected root cause, and assignee for the fix; set a resolution target of no more than 2 sprints.
8. Post in the team Slack channel linking to the ticket so the owning team is aware.

## Validation

- The flaky test is catalogued in the tracking system with evidence of the failure pattern
- The test is quarantined in CI with a comment pointing to the tracking ticket
- Other pull requests on the affected repository are no longer blocked by this test
- The tracking ticket has an assigned owner and a target resolution date

## Rollback

1. If quarantining the test reveals it was masking a real regression, remove it from the skip list and escalate the underlying issue as a bug.
2. If the quarantine was applied incorrectly to a test that was failing due to a legitimate code change, revert the skip-list change and direct the author to fix the code.
3. If the test was incorrectly identified as flaky and actually has a deterministic failure cause, remove it from the flaky test catalogue and reopen the original bug investigation.
