---
id: SYSTEM-033
type: system
title: Deployment Controller
status: approved
owner: CI/CD Engineering
owner_team: CI/CD Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2025-05-06T10:40:35.688Z'
updated: '2025-10-17T05:16:51.490Z'
tags:
  - system
  - ci-cd-platform
summary: Deployment Controller
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/deployment-controller
dependencies:
  - Release Dashboard Service
  - Build Orchestration Service
runbooks:
  - RUNBOOK-049
  - RUNBOOK-043
example: true
---

## Overview

The Deployment Controller orchestrates the promotion and execution of deployments across all environments (staging, canary, production). It receives deployment requests from the release pipeline, verifies artifact integrity against the Artifact Registry, enforces approval gates, executes ArgoCD sync operations, and reports deployment state to the Release Dashboard Service.

The controller manages approximately 80 deployments per day and maintains a full audit log of every deployment decision, gate result, and rollback event.

## Architecture

- **API Layer**: RESTful endpoints for deployment requests, approval callbacks, rollback triggers, and status queries. Role-based access enforced per environment tier.
- **Gate Engine**: Configurable approval gates evaluated before each environment promotion. Gate types include: automated test results, manual approval, canary analysis score, and maintenance window compliance.
- **Execution Layer**: Issues ArgoCD Application sync requests and polls sync status. Performs health check polling post-sync. Triggers automated rollback if health checks fail within the configured window.
- **State Store**: OpenSearch indexes all deployment events for audit query and the Release Dashboard. Redis caches active deployment state for low-latency status reads.
- **Notification Layer**: Publishes deployment events to Slack channels and PagerDuty on failure or rollback.

## Repositories

- [deployment-controller](https://git.example.com/acme/deployment-controller) - Application code, gate configuration schemas, Dockerfile

## Runtime Environment

- **Platform**: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
- **Deployment**: Blue-green via ArgoCD
- **Configuration**: AWS SSM for approval gate configurations, Kubernetes Secrets for ArgoCD API tokens

## Dependencies

- Release Dashboard Service - receives deployment event stream
- Build Orchestration Service - triggers deployment on successful build
- OpenSearch - deployment audit log index
- Redis 7 - active deployment state cache

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Gate evaluation latency | P95 < 10s |
| Rollback execution time | P95 < 3 minutes from trigger |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-049|Deployment Controller Runbook]]
- [[RUNBOOK-043|Deployment Gate Failure Runbook]]
