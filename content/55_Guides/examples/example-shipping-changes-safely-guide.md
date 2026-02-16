---
id: shipping-changes-safely-guide
type: guide
title: How to Ship Changes Safely
status: approved
owner: Engineering Team
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - guide
  - deployments
  - onboarding
summary: >-
  Teaches new engineers how production deployments work at our company -
  the concepts, tools, and mental model. USE A GUIDE when you need to
  TEACH someone something: explain concepts, build understanding, walk
  through workflows at a conceptual level. Guides are educational and
  audience-focused. They answer "how does this work?" not "do these
  exact steps." Compare: a Process defines who does what and when
  (governance); an SOP gives the exact procedure to execute (operations);
  a Runbook tells you what to do when something breaks (incidents).
  A Guide teaches you enough to understand all three.
audience: internal
related_systems:
  - payments-api-system
related_sops:
  - deploy-with-rollback-sop
example: true
---

## Why This Matters

Every change to production carries risk. A bad deploy can take down the payments system, block customers from checking out, or corrupt data that takes days to recover. Our deployment process exists to make shipping fast AND safe.

This guide explains how our deployment pipeline works end-to-end so you understand the *why* behind each step. For the exact commands to run, see the [[example-production-deployment-sop|Production Deployment SOP]]. For what to do if a deploy goes wrong, see the [[example-service-outage-runbook|Service Outage Runbook]].

## The Mental Model

Think of shipping a change as three phases:

1. **Before** - Get your change reviewed and approved (the [[example-change-management-process|Change Management Process]] governs this)
2. **During** - Execute the deployment (the [[example-production-deployment-sop|Production Deployment SOP]] has the exact steps)
3. **After** - Monitor and verify (or respond to incidents via [[example-service-outage-runbook|Runbooks]])

This guide covers the concepts behind all three phases.

## How Our Pipeline Works

### Build and Test

When you merge a PR to `main`, CI automatically:

- Runs the full test suite (unit, integration, E2E)
- Builds a Docker image tagged with the commit SHA
- Pushes the image to our container registry
- Generates a deployment manifest

You don't need to do anything here. If CI fails, the merge is blocked.

### The Change Ticket

Before deploying, you need an approved change ticket. This isn't bureaucracy - it's how we:

- Track what changed and why (audit trail)
- Ensure someone besides you reviewed the risk
- Coordinate timing so deploys don't collide

For low-risk changes (config updates, small bug fixes), approval is lightweight - your PR reviewer can approve the ticket. For high-risk changes (database migrations, new services, breaking API changes), you need a senior engineer's sign-off.

### The Deploy Itself

We use blue-green deployments. This means:

- The new version spins up alongside the old one
- Health checks verify the new version is healthy
- Traffic gradually shifts from old to new
- If anything looks wrong, traffic shifts back instantly

The key insight: **rollback is always one click away**. You don't need to "fix forward" under pressure. If metrics degrade, roll back first, investigate second.

### Monitoring Window

After a deploy, we watch metrics for 15 minutes:

- **Error rate**: Should stay below 0.1%. Any spike above 1% triggers rollback.
- **Latency**: P95 should stay under 500ms. Sustained increase above 1s triggers rollback.
- **Business metrics**: Order completion rate, payment success rate should stay stable.

If you're unsure whether a metric looks normal, check the dashboards linked in the [[example-service-outage-runbook|Service Outage Runbook]] for baseline comparisons.

## Common Questions

### "Can I deploy on Friday afternoon?"

We have a soft freeze Friday after 3pm. You can deploy with senior engineer approval, but ask yourself: do you want to be debugging at 7pm on a Friday?

### "What if my change needs a database migration?"

Database migrations are always high-risk. They need:
- A tested rollback migration
- Off-peak deployment window
- DBA review for anything touching indexes or large tables

See the database migration section of the [[example-production-deployment-sop|Deployment SOP]] for the exact procedure.

### "How do I know if my change is high-risk?"

If any of these are true, it's high-risk:
- Database schema changes
- New external service dependencies
- Changes to authentication or authorization
- Breaking API changes (even behind feature flags)
- Infrastructure changes (new queues, new caches, scaling config)

## Next Steps

- Read the [[example-change-management-process|Change Management Process]] to understand the governance workflow
- Bookmark the [[example-production-deployment-sop|Production Deployment SOP]] for when you're ready to deploy
- Familiarize yourself with the [[example-service-outage-runbook|Service Outage Runbook]] before your first on-call rotation
