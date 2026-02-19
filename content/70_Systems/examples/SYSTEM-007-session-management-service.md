---
id: SYSTEM-007
type: system
title: Session Management Service
status: review
owner: User Engineering
owner_team: User Engineering
runtime: Kubernetes / TypeScript / PostgreSQL 16 / Redis 7
created: '2024-09-27T15:24:53.020Z'
updated: '2026-02-24T15:01:16.549Z'
tags:
  - system
  - user-authentication
summary: Session Management Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/session-management-service
dependencies:
  - Identity Provider Service
  - User Directory Service
runbooks:
  - RUNBOOK-008
  - RUNBOOK-010
example: true
---

## Overview

The Session Management Service is responsible for creating, validating, and terminating user sessions across the platform. It issues session tokens upon successful authentication, enforces session timeouts, and supports concurrent session limits per user account.

The service handles approximately 800,000 session validations per day with a peak of 1,200 requests per second during morning login hours. Sessions are stored in Redis for sub-millisecond lookup and backed by PostgreSQL for audit trails and session history queries.

## Architecture

The service uses an event-driven architecture with a thin HTTP layer and a Redis-backed session store:

- **API Layer**: REST endpoints for session creation, validation, refresh, and termination. All endpoints are mTLS-authenticated between services.
- **Session Store**: Redis 7 cluster with key expiry used to enforce absolute and sliding session timeouts. Session data is serialized as MessagePack for compact storage.
- **Audit Layer**: All session lifecycle events are written to PostgreSQL 16 asynchronously via an internal event queue, providing a durable audit trail.
- **Concurrency Control**: Per-user session counts are tracked in Redis using atomic increment/decrement operations. Exceeding the configured limit invalidates the oldest active session.
- **Token Format**: Sessions are identified by cryptographically random 256-bit tokens (base64url-encoded). No session state is embedded in the token.

## Repositories

- [session-management-service](https://git.example.com/acme/session-management-service) - Application code, migrations, Dockerfile, Helm chart

## Runtime Environment

- **Platform**: Kubernetes across 3 availability zones
- **Language**: TypeScript (Node.js 20 LTS)
- **Replicas**: 3 pods minimum, autoscaling to 10 based on request rate
- **Resources**: 256Mi memory request / 512Mi limit, 250m CPU request / 500m limit per pod
- **Deployment**: Rolling updates via ArgoCD with readiness probe gates
- **Configuration**: Secrets via Kubernetes Secrets with 30-day rotation for Redis auth credentials

## Dependencies

- Redis 7 cluster (3 nodes) — primary session store, TTL-based expiry for session timeouts
- PostgreSQL 16 (primary + 1 read replica) — audit log and session history
- Identity Provider Service — validates identity tokens before issuing sessions
- User Directory Service — looks up account configuration (max sessions, timeout policy)

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Latency (validation) | P50 < 5ms, P99 < 20ms |
| Latency (creation) | P50 < 30ms, P99 < 80ms |
| Error rate | < 0.05% 5xx responses |
| Recovery | MTTR < 15 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-008|Session Service Outage Runbook]]
- [[RUNBOOK-010|Session Store Degradation Runbook]]
