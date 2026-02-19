---
id: SYSTEM-016
type: system
title: Notification Routing Engine
status: review
owner: Notification Engineering
owner_team: Notification Engineering
runtime: Kubernetes / TypeScript / PostgreSQL 16 / Redis 7
created: '2024-04-13T11:33:42.464Z'
updated: '2026-06-12T11:02:22.117Z'
tags:
  - system
  - notification-service
summary: Notification Routing Engine
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/notification-routing-engine
dependencies:
  - Push Notification Gateway
  - Email Delivery Service
runbooks:
  - RUNBOOK-022
  - RUNBOOK-023
example: true
---

## Overview

The Notification Routing Engine is the central dispatch service responsible for receiving notification requests from upstream producers and determining the appropriate delivery channel for each message. It evaluates user preferences, notification type, priority level, and channel availability to route each notification to the correct downstream delivery service.

The engine processes approximately 200,000 notifications per day across email, push, and SMS channels. It integrates with the Push Notification Gateway and Email Delivery Service as primary delivery targets, applying routing rules stored in PostgreSQL and cached in Redis for low-latency decisions.

## Architecture

The service follows a pipeline architecture with pluggable channel adapters:

- **API Layer**: RESTful and event-driven ingestion endpoints. Accepts notification requests via HTTP POST and RabbitMQ queue subscriptions. JWT-authenticated for HTTP paths.
- **Rules Engine**: Evaluates routing rules in priority order. Checks user opt-out status, channel-specific rate limits, quiet hours, and notification category preferences before selecting a channel.
- **Channel Adapter Layer**: Thin adapter interfaces for each downstream channel (email, push, SMS). Each adapter handles serialization and enqueuing to the appropriate delivery service.
- **Data Layer**: PostgreSQL stores routing rules, delivery logs, and channel configuration. Redis caches user preference lookups (TTL: 5 minutes) and deduplication keys (TTL: 24 hours).
- **Event Layer**: Publishes delivery outcome events to RabbitMQ for analytics and retry consumers.

## Repositories

- [notification-routing-engine](https://git.example.com/acme/notification-routing-engine) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: TypeScript / Node.js 20 LTS
- **Replicas**: 3 pods minimum, autoscaling to 9 based on queue depth
- **Resources**: 256Mi memory request / 512Mi limit, 250m CPU request / 500m CPU limit per pod
- **Deployment**: Rolling via ArgoCD with readiness probe gates
- **Configuration**: Environment variables via ConfigMaps, secrets via Kubernetes Secrets
- **TLS**: Terminated at the ingress controller, mTLS between services via service mesh

## Dependencies

- PostgreSQL 16 cluster (primary + 1 read replica) - routing rules and delivery log storage
- Redis 7 - user preference cache and deduplication key store
- Push Notification Gateway - downstream push delivery
- Email Delivery Service - downstream email delivery
- RabbitMQ - inbound notification queue and outbound outcome events

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Routing latency | P95 < 100ms per routing decision |
| Throughput | 500 notifications/second sustained |
| Error rate | < 0.2% routing failures under normal conditions |

## Runbooks

- [[RUNBOOK-022|Notification Routing Engine - High Error Rate]]
- [[RUNBOOK-023|Notification Routing Engine - Queue Backlog]]
