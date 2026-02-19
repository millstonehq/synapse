---
id: SYSTEM-035
type: system
title: Release Dashboard Service
status: review
owner: CI/CD Engineering
owner_team: CI/CD Engineering
runtime: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
created: '2025-04-09T18:24:51.479Z'
updated: '2025-03-14T02:17:08.858Z'
tags:
  - system
  - ci-cd-platform
summary: Release Dashboard Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/release-dashboard-service
dependencies:
  - CI Runner Fleet Manager
  - Artifact Registry
runbooks:
  - RUNBOOK-048
  - RUNBOOK-077
example: true
---

## Overview

The Release Dashboard Service provides real-time and historical visibility into the state of all deployments across the CI/CD platform. It aggregates events from the CI Runner Fleet Manager, Artifact Registry, and Deployment Controller to present a unified view of build status, deployment progress, environment health, and release history for engineering and product teams.

The dashboard serves approximately 400 daily active users and processes around 15,000 inbound events per day from upstream services.

## Architecture

- **Event Ingestion**: Consumes build completion, artifact push, and deployment lifecycle events via a PostgreSQL-backed event stream. Redis caches the latest known state per service per environment for low-latency dashboard reads.
- **API Layer**: RESTful and Server-Sent Events (SSE) endpoints. REST endpoints serve historical queries. SSE streams push live deployment state updates to connected browser clients.
- **Query Engine**: PostgreSQL 15 with time-series-optimized indexes for deployment history, lead time, and failure rate queries. Pre-aggregated daily rollups reduce query cost for report views.
- **Notification Hooks**: Supports webhook configuration per team for deployment success/failure events. Integrates with Slack and PagerDuty for critical failure notifications.

## Repositories

- [release-dashboard-service](https://git.example.com/acme/release-dashboard-service) - Application code, migrations, frontend assets, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
- **Replicas**: 2 pods minimum, autoscaling to 6 based on SSE connection count
- **Deployment**: Blue-green via ArgoCD

## Dependencies

- CI Runner Fleet Manager - build status events
- Artifact Registry - artifact promotion events
- PostgreSQL 15 - event store and aggregated metrics
- Redis 7 - live deployment state cache

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Dashboard load time | P95 < 1.5s |
| Event-to-display latency | P95 < 5s from event to visible state change |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-048|Release Dashboard Runbook]]
- [[RUNBOOK-077|CI Build Artifact Corruption Runbook]]
