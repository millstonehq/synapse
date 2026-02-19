---
id: PROCESS-050
type: process
title: Customer Portal Release Process
status: approved
owner: Engineering Manager
created: '2025-03-27T14:59:59.829Z'
updated: '2025-02-02T20:19:23.134Z'
tags:
  - process
  - customer-portal
summary: Customer Portal Release Process
related_standards:
  - STANDARD-049
  - STANDARD-050
related_sops:
  - SOP-087
  - SOP-085
related_systems:
  - SYSTEM-045
example: true
---

## Purpose

This process governs the end-to-end lifecycle of a Customer Portal release from development completion through production deployment and post-release validation. It establishes the checkpoints, approval gates, and communication steps required to ship portal changes safely while minimizing customer impact. The process applies to all scheduled releases and hotfixes.

## Scope

- All frontend and backend changes deployed to the Customer Portal production environment
- Database schema migrations associated with portal features
- Configuration and feature flag changes affecting portal behavior
- Third-party integration updates in the portal's dependency chain

## Roles and Responsibilities

- **Release Manager**: Coordinates the release schedule, owns the release ticket, and communicates status to stakeholders
- **Engineering Lead**: Verifies all feature branches are merged and CI is green on the release candidate
- **QA Engineer**: Executes regression test suite on staging; signs off on release readiness
- **On-Call Engineer**: Monitors production metrics during and after deployment; executes rollback if needed
- **Product Manager**: Confirms release scope matches sprint commitments; approves customer communication

## Triggers

- Sprint end date is reached and the release candidate is ready for staging validation
- An urgent hotfix is required outside the normal sprint cycle
- A dependency security patch requires an out-of-band release

## Inputs

- Merged feature branches with passing CI on `main`
- QA sign-off from staging regression tests
- Approved change ticket with rollback plan documented
- Customer communication draft approved by product manager

## Outputs

- Successfully deployed portal version in production with verified metrics
- Updated status page and release notes published
- Completed change ticket with deployment evidence
- Stakeholder notification of successful release

## Steps

1. Engineering Lead confirms all sprint items are merged to `main` and CI is green; creates release candidate tag
2. Release Manager opens the release ticket, documents scope, and links to change ticket
3. QA Engineer deploys release candidate to staging environment and executes full regression suite
4. QA Engineer logs any blocking issues; engineering triages and resolves before proceeding
5. Release Manager requests approval from Engineering Lead and Product Manager on the release ticket
6. Release Manager schedules deployment within the approved maintenance window and notifies on-call
7. On-Call Engineer executes deployment per the [[SOP-087|Debug Customer Session Issue SOP]] deployment steps and monitors for 15 minutes
8. Release Manager publishes release notes and updates the status page; sends stakeholder notification

## Controls

- No deployment without QA sign-off and an approved change ticket
- Deployments on Fridays after 3pm require explicit Engineering Manager approval
- Failed deployments must trigger rollback within 10 minutes of SLO breach
