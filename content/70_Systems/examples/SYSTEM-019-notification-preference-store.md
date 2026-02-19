---
id: SYSTEM-019
type: system
title: Notification Preference Store
status: approved
owner: Notification Engineering
owner_team: Notification Engineering
runtime: Kubernetes / TypeScript / PostgreSQL 16 / Redis 7
created: '2024-08-30T17:08:32.323Z'
updated: '2025-11-03T16:19:39.044Z'
tags:
  - system
  - notification-service
summary: Notification Preference Store
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/notification-preference-store
dependencies:
  - Email Delivery Service
  - Push Notification Gateway
runbooks:
  - RUNBOOK-027
  - RUNBOOK-028
example: true
---

## Overview

The Notification Preference Store is the authoritative source for per-user notification preferences across all channels and categories. It provides a REST API allowing users and internal services to read and write preferences including channel opt-outs, frequency caps, quiet hours, and per-category subscriptions.

All delivery services consult this store before dispatching a notification. The preference store is designed for high read throughput with low write frequency, using a read-through cache to serve the majority of traffic without hitting the database. Preference changes written by users are propagated to the cache within 30 seconds.

## Architecture

The service follows a read-optimized CRUD pattern:

- **API Layer**: RESTful endpoints for reading and updating preferences. Authenticated via JWT for user-facing calls; service-to-service calls use mTLS with service account tokens.
- **Cache Layer**: Redis stores serialized preference objects per user ID. TTL is 5 minutes with explicit invalidation on write. Cache miss falls through to the PostgreSQL primary.
- **Data Layer**: PostgreSQL stores the full preference record per user. Schema supports per-channel flags, per-category subscriptions, quiet hours (start/end time + timezone), and daily/weekly frequency caps.
- **Audit Log**: Every preference change is appended to an immutable `preference_events` table for compliance and debugging.
- **Event Publisher**: Publishes preference change events to RabbitMQ so downstream services can update their own caches proactively.

## Repositories

- [notification-preference-store](https://git.example.com/acme/notification-preference-store) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: TypeScript / Node.js 20 LTS
- **Replicas**: 2 pods minimum, autoscaling to 6 based on CPU
- **Resources**: 256Mi memory request / 512Mi limit, 250m CPU request / 500m CPU limit per pod
- **Deployment**: Rolling via ArgoCD
- **Configuration**: Environment variables via ConfigMaps; database credentials via Kubernetes Secrets

## Dependencies

- PostgreSQL 16 cluster (primary + 1 read replica) - preference records and audit log
- Redis 7 - read-through preference cache
- RabbitMQ - outbound preference change events
- Email Delivery Service and Push Notification Gateway - primary consumers of preference data

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Read latency | P95 < 20ms (cache hit), P95 < 100ms (cache miss) |
| Write latency | P95 < 200ms |
| Cache propagation | Preference changes reflected in cache within 30 seconds |

## Runbooks

- [[RUNBOOK-027|Email Delivery Service - Provider Failover]]
- [[RUNBOOK-028|Push Notification Gateway - Token Invalidation Spike]]
