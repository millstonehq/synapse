---
id: PROCESS-024
type: process
title: Notification Service Release Process
status: review
owner: Platform Lead
created: '2024-09-10T00:18:30.061Z'
updated: '2025-07-07T06:42:34.152Z'
tags:
  - process
  - notification-service
summary: Notification Service Release Process
related_standards:
  - STANDARD-020
  - STANDARD-023
related_sops:
  - SOP-037
  - SOP-034
related_systems:
  - SYSTEM-018
example: true
---

## Purpose

This process governs how code, configuration, and template changes are released to the production Notification Service. Given that the service handles user-facing communications for multiple channels, releases must be carefully coordinated to avoid delivery disruptions, compliance regressions, or silent failures.

## Scope

- All application code deployments to the Notification Service
- Template registry updates that affect production notification flows
- Configuration changes to routing rules, rate limits, provider credentials, and retry policies

## Roles and Responsibilities

- **Release Engineer**: Owns the release ticket, coordinates timing, and executes the deployment
- **On-Call Engineer**: Monitors alerting dashboards during and after the release
- **Platform Lead**: Approves releases classified as high-risk (schema changes, provider configuration, rate limit changes)
- **QA Engineer**: Validates staging smoke tests pass before production promotion

## Triggers

- A feature branch is merged to main and CI passes
- A template change is approved through the template approval process
- An urgent fix is needed for a production defect affecting delivery

## Inputs

- Merged pull request with passing CI and at least one peer review
- Release ticket documenting the change, risk level, and rollback plan
- Staging smoke test results confirming expected notification delivery behavior

## Outputs

- Deployed service version with verified health metrics
- Completed release ticket with commit SHA, deployment timestamp, and post-deploy verification screenshot
- Updated monitoring baseline if delivery metrics changed materially

## Steps

1. Release Engineer creates a release ticket, classifies risk level, and documents the rollback plan
2. QA Engineer runs the notification smoke test suite in staging and confirms all channels deliver correctly
3. Platform Lead approves high-risk releases; peer review is sufficient for low/medium risk
4. Release Engineer announces the release in #notifications-releases and confirms on-call engineer is monitoring
5. Release Engineer deploys using the blue-green deployment workflow and monitors the rollout
6. On-Call Engineer watches delivery rate, error rate, and queue depth for 15 minutes post-deploy
7. Release Engineer marks the ticket complete with deployment evidence and notifies stakeholders

## Controls

- Releases must not be initiated within 2 hours of a known high-volume sending window (e.g., scheduled campaigns)
- Schema-breaking changes to the notification payload format require a deprecation window of at least 2 weeks
- Failed deployments trigger automatic rollback and a mandatory post-release review within 48 hours
- Release tickets are retained for 12 months for audit purposes
