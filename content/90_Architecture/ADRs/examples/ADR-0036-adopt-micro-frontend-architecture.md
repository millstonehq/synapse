---
id: ADR-0036
type: adr
title: Adopt Micro-Frontend Architecture
status: approved
owner: Principal Engineer
created: '2025-12-13T01:17:21.835Z'
updated: '2025-08-06T17:34:17.913Z'
tags:
  - adr
  - customer-portal
summary: Adopt Micro-Frontend Architecture
example: true
---

## Context

The Customer Portal is being developed by multiple product teams: the Core Portal team owns the account overview and settings pages; the Support team owns the support widget and ticket management; the Analytics team owns the customer insights dashboard. As the portal has grown, all three teams contribute code to the same Next.js monolith, resulting in merge conflicts, slow CI times (18 minutes for the full test suite), and cross-team blocking on releases.

The Support team wants to ship their widget improvements on their own release schedule, but today a portal release requires all three teams to coordinate and sign off simultaneously. The Analytics team has a different technology preference (they prefer a Svelte-based dashboard) that cannot be accommodated in a monolith.

The teams evaluated architectural options to enable independent development and deployment while maintaining a unified user experience.

## Decision

Adopt a **micro-frontend architecture** for the Customer Portal using **Module Federation** (Webpack 5 / Next.js).

Each product team owns a separate Next.js application (remote) that exposes its components via Module Federation. The Core Portal team maintains the shell application (host) that composes the remotes into a unified layout. The Support Widget and Analytics Dashboard are loaded as federated modules at runtime.

## Consequences

**Positive:**
- Each team can deploy their remote application independently without coordinating a portal-wide release
- Teams can use different dependency versions within their remote (within federation compatibility constraints)
- CI is split per team; each team's CI only runs tests for their remote — build times drop from 18 minutes to under 5 minutes per team
- Failures in one remote are isolated and do not take down the entire portal if remotes load asynchronously

**Negative:**
- Module Federation adds runtime complexity; shared dependency version conflicts can cause subtle bugs
- The shell/remote coordination model requires a contract for exposed module interfaces; breaking changes in a remote break the shell
- Debugging across module boundaries is harder than debugging a monolith
- Total JavaScript bundle may increase if common dependencies are not properly shared

**Neutral:**
- Each team still uses React and the same shared design system package; the architecture change is at the deployment boundary, not the component level
- TypeScript types need to be shared across team boundaries via a shared types package

## Alternatives Considered

**iFrame-based composition:**
- Pro: Maximum isolation; no shared dependency concerns; each team fully independent
- Con: iFrame UX limitations (no seamless scroll, focus management complexity, CSP configuration overhead); poor accessibility
- Rejected because: The support widget in an iframe already causes accessibility issues (this ADR is partly motivated by improving on that); extending iframes to more portal areas would compound the problem.

**Monorepo with shared CI but independent deploys via feature flags:**
- Pro: No new architecture complexity; teams still work in one repo but gate their own features
- Con: Does not solve the 18-minute CI problem; all teams still block on each other for releases even with feature flags
- Rejected because: The core problem is release coupling, not code colocation. Feature flags do not remove the requirement for cross-team release sign-off.
