---
id: SYSTEM-031
type: system
title: Build Orchestration Service
status: approved
owner: CI/CD Engineering
owner_team: CI/CD Engineering
runtime: Kubernetes / Node.js 20 / PostgreSQL 16
created: '2024-06-28T12:18:03.568Z'
updated: '2025-11-15T14:37:37.481Z'
tags:
  - system
  - ci-cd-platform
summary: Build Orchestration Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/build-orchestration-service
dependencies:
  - Release Dashboard Service
  - CI Runner Fleet Manager
runbooks:
  - RUNBOOK-048
  - RUNBOOK-046
example: true
---

## Overview

The Build Orchestration Service is the central coordinator for all CI/CD build jobs across the platform. It receives build trigger events (from Git webhooks, manual dispatches, and scheduled runs), queues work onto the CI Runner Fleet, tracks job state, and aggregates results for downstream consumers such as the Release Dashboard.

The service handles approximately 8,000 build jobs per day with peak throughput of 120 concurrent jobs during business hours. It coordinates with the CI Runner Fleet Manager to schedule jobs onto available runners and publishes build completion events to downstream services.

## Architecture

- **API Layer**: RESTful and webhook endpoints for build triggers, job status queries, and result callbacks. JWT-authenticated for API calls, HMAC-signed for webhook events.
- **Queue Layer**: RabbitMQ-backed job queue with priority lanes (urgent, standard, background). Dead-letter queue captures failed dispatch attempts for retry.
- **State Layer**: PostgreSQL tracks job lifecycle (queued → dispatched → running → success/failure/cancelled). Row-level locking prevents double-dispatch.
- **Event Layer**: Publishes `build.completed`, `build.failed`, and `build.cancelled` events on success or terminal state transitions for the Release Dashboard and artifact pipeline.
- **Runner Interface**: Communicates with the CI Runner Fleet Manager to dispatch jobs, receive heartbeats, and reclaim abandoned jobs from stale runners.

## Repositories

- [build-orchestration-service](https://git.example.com/acme/build-orchestration-service) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Node.js 20 / PostgreSQL 16
- **Replicas**: 3 pods minimum, autoscaling to 8 based on queue depth
- **Deployment**: Rolling via ArgoCD with readiness checks on the queue consumer
- **Configuration**: ConfigMaps for tunable thresholds, Kubernetes Secrets for webhook signing keys

## Dependencies

- CI Runner Fleet Manager - job dispatch and heartbeat receiver
- Release Dashboard Service - consumes build completion events
- PostgreSQL 16 - job state persistence
- RabbitMQ 3.13 - job queue and dead-letter handling

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Job dispatch latency | P95 < 5s from trigger to runner pickup |
| Error rate | < 0.5% failed dispatches under normal load |
| Recovery | MTTR < 20 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-048|Build Orchestration Service Runbook]]
- [[RUNBOOK-046|CI Queue Backlog Runbook]]
