---
id: SYSTEM-018
type: system
title: Push Notification Gateway
status: review
owner: Notification Engineering
owner_team: Notification Engineering
runtime: Kubernetes / .NET 8 / SQL Server 2022
created: '2025-11-05T10:55:03.454Z'
updated: '2026-08-07T10:15:24.589Z'
tags:
  - system
  - notification-service
summary: Push Notification Gateway
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/push-notification-gateway
dependencies:
  - Notification Routing Engine
  - SMS Dispatch Service
runbooks:
  - RUNBOOK-074
  - RUNBOOK-028
example: true
---

## Overview

The Push Notification Gateway is the platform service responsible for delivering push notifications to iOS and Android devices. It receives dispatch requests from the Notification Routing Engine, validates device token registrations, and forwards messages to Apple Push Notification service (APNs) and Firebase Cloud Messaging (FCM) as appropriate.

The gateway manages device token lifecycle, including registration, renewal, and invalidation upon delivery failure. It supports both transactional (immediate, high-priority) and marketing (batched, lower-priority) push notification classes, applying the correct APNs/FCM priority flags for each.

## Architecture

The service is built on .NET 8 with a worker-service pattern:

- **API Layer**: REST endpoints for device token registration/deregistration and direct push dispatch. Used by mobile clients for token management and by the routing engine for dispatch.
- **Dispatch Worker**: Consumes from the push notification queue. Batches messages by platform (iOS vs. Android) for efficient provider calls. Implements exponential backoff retry for transient provider errors.
- **Platform Adapter Layer**: APNs adapter using HTTP/2 with JWT authentication. FCM adapter using the v1 HTTP API with OAuth2 service account credentials.
- **Token Registry**: SQL Server table tracking device tokens, last-seen timestamp, platform, and validity status. Invalid tokens (indicated by provider feedback) are marked inactive and excluded from future sends.
- **Data Layer**: SQL Server for token registry and delivery records. Redis for in-flight deduplication keys.

## Repositories

- [push-notification-gateway](https://git.example.com/acme/push-notification-gateway) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: C# / .NET 8
- **Replicas**: 3 pods minimum, autoscaling to 10 based on queue depth
- **Resources**: 512Mi memory request / 1Gi limit, 500m CPU request / 1 CPU limit per pod
- **Deployment**: Blue-green via ArgoCD
- **Configuration**: appsettings.json overlaid by environment-specific ConfigMaps; APNs private key and FCM credentials via Kubernetes Secrets

## Dependencies

- SQL Server 2022 - device token registry, delivery records
- Redis 7 - deduplication keys, provider health status
- APNs (Apple Push Notification service) - iOS push delivery
- FCM (Firebase Cloud Messaging) - Android push delivery
- Notification Routing Engine - inbound dispatch jobs

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Dispatch latency | P95 < 2s from job receipt to provider submission |
| Delivery acceptance | > 99% of valid-token sends accepted by APNs/FCM |
| Error rate | < 0.5% unretryable failures under normal conditions |

## Runbooks

- [[RUNBOOK-074|Notification Template Rendering Failure Runbook]]
- [[RUNBOOK-028|Push Notification Gateway - Token Invalidation Spike]]
