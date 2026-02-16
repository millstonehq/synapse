---
id: change-management-process
type: process
title: Change Management Process
status: approved
owner: Engineering Manager
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - process
  - deployments
  - governance
summary: >-
  Defines how production changes are proposed, reviewed, approved,
  executed, and verified across the organization. USE A PROCESS when you
  need to define an org-level WORKFLOW: who is responsible for what, what
  triggers the workflow, what goes in and comes out, and what controls
  exist. Processes answer "how does our organization handle X?" They
  define roles, accountability, and governance - not the exact buttons
  to click. Compare: an SOP gives the detailed procedure to execute
  a specific step within this process; a Runbook handles when things
  go wrong during the process; a Guide teaches someone the concepts
  behind the process.
related_standards:
  - change-control-standard
related_sops:
  - deploy-with-rollback-sop
related_systems:
  - payments-api-system
example: true
---

## Purpose

Ensure all production changes are reviewed, approved, traceable, and reversible. This process reduces the risk of outages caused by uncoordinated or untested changes while maintaining development velocity.

## Scope

All changes to production systems, including:

- Application code deployments
- Database schema migrations
- Infrastructure configuration changes (Kubernetes manifests, Terraform)
- Third-party service integrations
- Feature flag changes that affect production behavior

**Out of scope:** Development and staging environment changes, documentation updates, and CI/CD pipeline changes that don't affect production behavior.

## Roles and Responsibilities

- **Change Owner** - The engineer who authored the change. Responsible for: creating the change ticket, providing risk assessment, executing the deployment, and monitoring post-deploy.
- **Reviewer** - A peer engineer who reviews the code and deployment plan. Responsible for: verifying test coverage, checking for regressions, and approving low-risk changes.
- **Approver** - A senior engineer or tech lead. Required for high-risk changes. Responsible for: evaluating blast radius, confirming rollback plan viability, and approving the maintenance window.
- **On-Call Engineer** - The engineer on rotation during the deployment. Responsible for: monitoring alerts during and after the deployment, initiating incident response if needed.

## Triggers

- A pull request is merged to `main` that requires production deployment
- A scheduled maintenance task requires production changes
- An urgent hotfix is needed for a production incident (expedited path)
- Infrastructure scaling or configuration changes are requested

## Inputs

- Merged pull request with passing CI
- Change ticket with: description of change, risk level (low/medium/high), rollback plan, estimated deployment window
- For high-risk changes: approval from Approver role
- For database migrations: DBA review sign-off

## Outputs

- Deployed change in production with verified health
- Completed change ticket with deployment record (commit SHA, deploy time, verifier)
- Updated monitoring dashboards reflecting new baseline (if metrics changed)
- Post-incident report (only if rollback was triggered)

## Steps

1. **Change Owner** creates a change ticket linked to the merged PR, selects risk level, and documents the rollback plan
2. **Reviewer** verifies the change ticket is complete and the risk level is accurate. For low-risk changes, Reviewer approves directly. For high-risk changes, Reviewer escalates to Approver
3. **Approver** (high-risk only) reviews blast radius, confirms rollback plan is tested, and approves a specific maintenance window
4. **Change Owner** announces the deployment in the #deployments channel, confirming the on-call engineer is available
5. **Change Owner** executes the deployment following the [[example-production-deployment-sop|Production Deployment SOP]]
6. **Change Owner** monitors health metrics for 15 minutes post-deploy. If SLOs degrade, initiates rollback per the SOP
7. **Change Owner** marks the change ticket as completed with deployment evidence (commit SHA, timestamp, health check screenshot)
8. **On-Call Engineer** continues monitoring for 1 hour post-deploy for delayed impact

## Controls

- No production deployment without an approved change ticket
- High-risk changes require Approver sign-off (enforced by deployment pipeline)
- All deployments must have a documented, tested rollback plan
- Change tickets are retained for 12 months for audit purposes
- Deployment pipeline blocks deploys if CI is failing on `main`
- Friday deploys after 3pm require senior engineer approval
- Failed deployments trigger mandatory post-incident review within 48 hours
