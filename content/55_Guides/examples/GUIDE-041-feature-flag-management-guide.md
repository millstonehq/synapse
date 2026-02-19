---
id: GUIDE-041
type: guide
title: Feature Flag Management Guide
status: approved
owner: Engineering Team
created: '2024-09-06T20:35:41.366Z'
updated: '2025-02-10T16:25:01.180Z'
tags:
  - guide
  - ci-cd-platform
summary: Feature Flag Management Guide
audience: internal
related_systems:
  - SYSTEM-033
example: true
---

## When to Use Feature Flags

Feature flags allow you to deploy code to production without exposing it to users — enabling continuous delivery of incomplete or high-risk features. Use a feature flag when:

- A feature is large enough to span multiple pull requests but you want to merge to main regularly rather than maintaining a long-lived feature branch
- You want to validate a new feature with a small percentage of users (gradual rollout) before full launch
- You need an instant kill switch to disable a feature if it causes unexpected behavior in production
- You are conducting an A/B test and need to control which users see which variant

Do not use feature flags for: environment-specific configuration (use environment variables instead), temporary logging (remove after the debugging session), or permanent feature gating (use a proper authorization system).

## Creating a Feature Flag

All feature flags must be registered in the feature flag service (LaunchDarkly or the internal flag service at `flags.internal`). Follow the naming convention: `<service>.<feature>.<type>` where type is one of `release`, `experiment`, or `ops`.

Example: `payments-api.new-checkout-flow.release`

When creating the flag:
- Set the **default value** to `false` (off) so the flag is safe to deploy before activation
- Record the **expected retirement date** — flags without a retirement date will be rejected
- Add a description explaining what the flag controls and which team owns it
- Set the initial rollout to 0% until ready to begin gradual activation

## Gradual Rollout Best Practices

Roll out gradually using traffic percentage targeting:

1. Start at 1% of users and monitor error rates and key business metrics for 30 minutes
2. If metrics are stable, increase to 10% and observe for another hour
3. Continue at 25%, 50%, and finally 100%, with observation periods at each increment
4. During each increment, have a clear abort criteria defined before you increase traffic (e.g., "if error rate increases by more than 0.5%, revert to 0%")

Always have the flag kill switch readily accessible during rollout — know how to quickly set it to 0% from your phone if needed during an incident.

## Retiring Flags Promptly

The most common source of feature flag debt is failing to clean up flags after full rollout. Once a flag has been at 100% for one sprint with stable metrics:

1. Remove all flag evaluation code from the application (the `if flag.isEnabled()` checks and the old code path)
2. Open a pull request with the cleanup, ensuring CI passes with the flag code removed
3. After the PR merges and deploys successfully, archive the flag in the flag service
4. Update the flag retirement record in the tracking system

Flags that are not retired within 90 days of reaching 100% rollout will be automatically flagged in the weekly platform review. Teams with more than 5 overdue flag retirements will be blocked from creating new flags until the backlog is cleared.
