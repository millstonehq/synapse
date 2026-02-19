---
id: PROCESS-038
type: process
title: Production Deployment Process
status: approved
owner: Engineering Manager
created: '2024-09-08T15:55:44.710Z'
updated: '2026-08-26T16:05:07.870Z'
tags:
  - process
  - ci-cd-platform
summary: Production Deployment Process
related_standards:
  - STANDARD-037
  - STANDARD-038
related_sops:
  - SOP-061
  - SOP-066
related_systems:
  - SYSTEM-031
example: true
---

## Purpose

This process defines the end-to-end workflow for deploying software changes to the production environment in a controlled, reviewable, and reversible manner. It ensures that every production deployment is associated with an approved change record, has passed all required CI gates, and is monitored post-deployment against defined SLOs. The process applies to both scheduled releases and urgent hotfixes, with differentiated approval paths for each.

## Scope

- Application service deployments triggered by merged pull requests to the main branch
- Infrastructure configuration changes applied to the production Kubernetes cluster
- Database schema migrations coordinated with application deployments
- Does not cover deployments to non-production environments, which follow a lighter-weight process

## Roles and Responsibilities

- **Change Owner**: Authors the change, creates the deployment record, selects the risk tier, executes the deployment, and monitors post-deploy health
- **Peer Reviewer**: Reviews the code and deployment plan, confirms test coverage is adequate, and approves low-risk deployments
- **Senior Engineer**: Required for medium and high-risk deployments; evaluates blast radius, confirms rollback plan, and approves the deployment window
- **On-Call Engineer**: Monitors alerts during and immediately after the deployment; initiates incident response if SLOs breach

## Triggers

- A pull request is merged to the main branch of a production service repository
- A scheduled infrastructure maintenance task is due for execution
- An emergency hotfix is authorized for a production incident (expedited path)

## Inputs

- Merged pull request with all CI stages passing (lint, test, build, security scan)
- Deployment record with: service name, change description, risk tier, rollback plan, and estimated deployment duration
- Signed and tagged container image in the approved registry
- For database migrations: tested migration script with documented rollback steps

## Outputs

- Service running the new version in production with confirmed healthy status
- Completed deployment record with commit SHA, deployment timestamp, and post-deploy health check evidence
- Updated monitoring baseline if any metrics thresholds were adjusted
- Incident report if rollback was triggered

## Steps

1. Change Owner creates a deployment record linked to the merged PR, selects the risk tier (low/medium/high), and documents the rollback plan
2. Peer Reviewer verifies the deployment record is complete, confirms CI passed, and approves low-risk deployments directly
3. Senior Engineer (medium/high-risk only) reviews the blast radius analysis and rollback plan, confirms the deployment window, and grants approval
4. Change Owner announces the deployment in #deployments: service name, commit SHA, deployment record ID, and on-call contact
5. Change Owner triggers the deployment via the GitOps controller and monitors pod rollout until all replicas are healthy
6. Change Owner checks the monitoring dashboard against pre-deployment baseline at 5, 10, and 15 minutes post-deploy
7. If any SLO breaches (error rate >1%, P95 latency >1s), Change Owner immediately initiates rollback per [[SOP-062|Roll Back Production Deployment SOP]]
8. Change Owner closes the deployment record with commit SHA, timestamp, and screenshot of stable health metrics

## Controls

- The CI/CD pipeline enforces that no deployment proceeds without a linked, approved deployment record
- Deployment records are immutable after closure and retained for 12 months
- Failed deployments trigger mandatory post-deploy review within 48 hours
- Friday deployments after 14:00 require explicit senior engineer approval
