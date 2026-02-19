---
id: ADR-0028
type: adr
title: Implement Trunk-Based Development
status: approved
owner: Staff Engineer
created: '2024-12-22T18:06:10.623Z'
updated: '2026-04-17T17:25:14.964Z'
tags:
  - adr
  - ci-cd-platform
summary: Implement Trunk-Based Development
example: true
---

## Context

Engineering teams were operating with a mixture of branching strategies: some teams used Gitflow with long-lived `develop` and `release` branches; others used feature branching with irregular integration cadences. The resulting integration pain was significant — teams regularly encountered merge conflicts requiring hours of resolution, and "integration freeze" periods before releases were a recognized problem. DORA metrics from the previous quarter showed a median lead time for changes of 4.8 days and a deployment frequency of fewer than 3 times per week per service.

The platform team identified branching strategy as a root cause of high integration overhead and slow deployment frequency. Research into high-performing engineering organizations consistently pointed to trunk-based development (TBD) — where all developers commit to a single shared branch (trunk/main) at least once per day — as a practice correlated with higher deployment frequency and lower change failure rates.

Adoption of TBD had been informally discussed but never formally decided. This ADR captures the organizational decision following a pilot with two teams over one quarter. Both pilot teams reported significant reduction in merge conflict resolution time and an increase in deployment frequency.

## Decision

Adopt **trunk-based development** as the standard branching strategy across all engineering teams.

All developers will commit to the `main` branch, either directly (for small changes) or via short-lived feature branches that are merged within 1–2 days of creation. Long-lived feature branches are prohibited; features that require more than 2 days of development must use feature flags to hide incomplete work from production traffic. Release branches are eliminated; releases are cut by tagging commits on `main`. The `main` branch is always in a deployable state; CI gates enforce this by requiring all tests to pass before merge.

Feature flags will be managed via our existing LaunchDarkly integration. Teams must clean up feature flags within 30 days of full rollout to prevent flag accumulation.

## Consequences

**Positive:**
- Lead time for changes decreases because code is integrated continuously rather than accumulated on long-lived branches
- Merge conflicts are smaller and more frequent, making them easier to resolve
- `main` is always deployable, enabling on-demand production deployments without a stabilization phase
- Improved visibility: all developers see each other's work as it lands, reducing surprise integrations

**Negative:**
- Requires feature flag discipline; incomplete features deployed behind flags add operational complexity if flags are not cleaned up
- Developers accustomed to Gitflow must change their habits; short-lived branches require frequent rebasing on `main`
- Test coverage quality becomes more critical because inadequate tests allow broken code to land on `main`

**Neutral:**
- Feature flag infrastructure (LaunchDarkly) was already in place; TBD formalizes its use rather than introducing a new tool
- Teams transitioning from Gitflow lose the separation of concerns between develop/release branches, but gain simpler Git history

## Alternatives Considered

**Continue with team-specific branching strategies:**
- Pro: Teams retain autonomy; no forced change to workflows; no migration cost
- Con: Integration pain and long lead times continue. No organization-wide improvement to DORA metrics. Different strategies make cross-team tooling standardization difficult.
- Rejected because: The status quo was producing measurably poor outcomes and the pilot data demonstrated that TBD adoption improved both lead time and developer satisfaction.

**Gitflow standardization (enforce one consistent Gitflow model):**
- Pro: Provides structure for release management; familiar to most engineers; works well for software with discrete release cycles
- Con: Long-lived branches inherently produce integration overhead. Deployment frequency is limited by release branch stabilization cycles. Not compatible with the goal of multiple deployments per day.
- Rejected because: Gitflow's release branch model is incompatible with high-frequency, continuous deployment to production. Standardizing Gitflow would entrench the low-frequency deployment pattern rather than improving it.
