---
id: CAPABILITY-019
type: capability
title: Continuous Delivery Capability
status: accepted
owner: VP Engineering
created: '2024-10-28T17:45:50.652Z'
updated: '2025-02-26T08:38:26.991Z'
tags:
  - capability
  - ci-cd-platform
summary: Continuous Delivery Capability
evidence_links:
  - STANDARD-041
  - PROCESS-039
  - STANDARD-042
example: true
---

## Domain

- Automated build, test, and release pipeline management across all service repositories
- Deployment gating controls including branch protection, CI checks, and approval workflows
- Release artifact management covering versioning, signing, and promotion between environments
- Rollback and recovery procedures for failed or degraded deployments
- DORA metrics collection and continuous improvement tracking for delivery performance

## Maturity (0-5)

- Pipeline Coverage: 3/5 - All production services have CI pipelines, but not all enforce required test coverage thresholds before merge
- Deployment Automation: 3/5 - Deployments to staging are fully automated; production releases still require a manual approval gate
- Rollback Capability: 3/5 - Rollback procedures are documented and tested quarterly, but automated rollback on failure is not yet implemented
- Metrics and Observability: 2/5 - Change failure rate and deployment frequency are tracked manually; no automated DORA dashboard exists
- Compliance Integration: 2/5 - Change tickets are required but pre-deploy compliance verification is not enforced by the pipeline

## Metrics

- Change failure rate: currently 8%, target below 5% within two quarters
- Deployment frequency: currently once per day per service, target multiple deployments per day
- Lead time for changes: currently 2 days from commit to production, target under 1 day
- Mean time to recovery: currently 2 hours, target under 30 minutes
- Percentage of deployments with automated rollback capability: currently 40%, target 100%

## Evidence Links

- [[STANDARD-041|Continuous Delivery Standard]] - Defines pipeline structure, branch protection rules, and required quality gates
- [[PROCESS-039|Release Management Process]] - Operational workflow for planning, approving, and executing production releases
- [[STANDARD-042|Deployment Compliance Standard]] - Controls for change ticket enforcement, environment promotion criteria, and rollback requirements

## Notes

- The gap from Level 3 to Level 4 is primarily blocked by the absence of an automated DORA metrics dashboard; this is tracked as a Q3 OKR deliverable
- Pre-deploy compliance checks that verify change ticket approval status before allowing a production deployment are planned for the next pipeline iteration
