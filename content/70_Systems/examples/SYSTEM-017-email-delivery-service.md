---
id: SYSTEM-017
type: system
title: Email Delivery Service
status: approved
owner: Notification Engineering
owner_team: Notification Engineering
runtime: Kubernetes / TypeScript / PostgreSQL 16 / Redis 7
created: '2025-07-15T17:55:20.515Z'
updated: '2025-02-16T03:22:35.570Z'
tags:
  - system
  - notification-service
summary: Email Delivery Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/email-delivery-service
dependencies:
  - SMS Dispatch Service
  - Notification Preference Store
runbooks:
  - RUNBOOK-027
  - RUNBOOK-024
example: true
---

## Overview

The Email Delivery Service is responsible for rendering, sending, and tracking all outbound email notifications on behalf of the Notification Platform. It receives pre-routed email jobs from the Notification Routing Engine, selects an appropriate email provider (SendGrid primary, Mailgun secondary), renders the template with recipient-specific data, and dispatches the message.

The service manages delivery receipts, bounce handling, and suppression list enforcement. It integrates with the Notification Preference Store to honor per-user opt-out and frequency cap settings before each send, ensuring compliance with CAN-SPAM and similar regulations.

## Architecture

The service is structured around a job consumer pattern:

- **Consumer Layer**: Pulls email jobs from the dedicated RabbitMQ queue. Acknowledges only after successful dispatch or permanent failure classification.
- **Template Engine**: Renders Handlebars templates stored in PostgreSQL. Supports per-locale variants and version-pinned template references.
- **Provider Adapter Layer**: Abstracts SendGrid and Mailgun behind a common `EmailProvider` interface. Circuit breaker triggers failover after 5 consecutive errors within 60 seconds.
- **Suppression Layer**: Checks the bounce, complaint, and unsubscribe lists stored in PostgreSQL before each send. Hard bounces are permanently suppressed; soft bounces are retried up to 3 times.
- **Data Layer**: PostgreSQL stores templates, suppression lists, and delivery records. Redis caches suppression lookups (TTL: 10 minutes) and provider health status.

## Repositories

- [email-delivery-service](https://git.example.com/acme/email-delivery-service) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: TypeScript / Node.js 20 LTS
- **Replicas**: 2 pods minimum, autoscaling to 6 based on queue depth
- **Resources**: 512Mi memory request / 1Gi limit, 500m CPU request / 1 CPU limit per pod
- **Deployment**: Rolling via ArgoCD
- **Configuration**: Environment variables via ConfigMaps; provider API keys via Kubernetes Secrets with 90-day rotation

## Dependencies

- PostgreSQL 16 cluster - templates, suppression lists, delivery records
- Redis 7 - suppression cache, deduplication keys
- SendGrid API - primary email provider
- Mailgun API - fallback email provider
- Notification Preference Store - opt-out and frequency cap enforcement

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Send latency | P95 < 5s from job receipt to provider submission |
| Delivery rate | > 98% of non-suppressed sends accepted by provider |
| Error rate | < 0.5% permanent failures under normal conditions |

## Runbooks

- [[RUNBOOK-027|Email Delivery Service - Provider Failover]]
- [[RUNBOOK-024|Email Delivery Service - High Bounce Rate]]
