---
id: SYSTEM-010
type: system
title: User Directory Service
status: approved
owner: User Engineering
owner_team: User Engineering
runtime: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
created: '2024-02-18T02:16:05.921Z'
updated: '2025-05-19T06:25:20.067Z'
tags:
  - system
  - user-authentication
summary: User Directory Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/user-directory-service
dependencies:
  - Session Management Service
  - Identity Provider Service
runbooks:
  - RUNBOOK-008
  - RUNBOOK-010
example: true
---

## Overview

The User Directory Service is the authoritative source of record for user accounts, profile data, organization memberships, and account status. It provides a gRPC and REST API used by downstream authentication services to look up user attributes, validate credentials during local auth flows, and manage account lifecycle events such as provisioning, suspension, and deletion.

The service manages approximately 2 million user records and handles 200,000 read requests per day. High-frequency reads (such as session validation lookups) are served from a Redis cache layer with a 5-minute TTL.

## Architecture

The service follows a repository pattern with a clear separation between the API, domain, and data layers:

- **gRPC API**: Primary interface for internal service-to-service communication. Exposes user lookup, credential validation, profile update, and account status change RPCs.
- **REST API**: Secondary interface for admin tooling and external integrations. Implements pagination and field projection to limit data exposure.
- **Cache Layer**: Redis 7 is used to cache frequently accessed user records. Cache entries are invalidated on write through a pub/sub invalidation channel.
- **Data Layer**: PostgreSQL 15 with full-text search indexes on name and email fields. Sensitive fields (password hashes, recovery codes) are stored in a separate schema with column-level encryption.
- **Event Emission**: Account lifecycle events (created, suspended, deleted) are published to the internal event bus for downstream consumers including audit and notification services.

## Repositories

- [user-directory-service](https://git.example.com/acme/user-directory-service) - Application code, migrations, Helm chart

## Runtime Environment

- **Platform**: Kubernetes across 3 availability zones
- **Language**: Go 1.22
- **Replicas**: 4 pods minimum, autoscaling to 12 based on CPU
- **Resources**: 512Mi memory request / 1Gi limit, 500m CPU request / 1 CPU limit per pod
- **Deployment**: Blue-green via ArgoCD
- **Encryption**: AES-256-GCM for sensitive column encryption; keys managed in HashiCorp Vault

## Dependencies

- PostgreSQL 15 (primary + 2 read replicas) — user record persistence
- Redis 7 — user record cache, cache invalidation pub/sub
- Session Management Service — session lookups reference user records
- Identity Provider Service — federated identity claims are reconciled with directory records

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Latency (read, cached) | P50 < 3ms, P99 < 10ms |
| Latency (read, uncached) | P50 < 20ms, P99 < 60ms |
| Latency (write) | P50 < 40ms, P99 < 120ms |
| Error rate | < 0.05% 5xx responses |

## Runbooks

- [[RUNBOOK-008|User Directory Availability Runbook]]
- [[RUNBOOK-010|User Directory Cache Degradation Runbook]]
