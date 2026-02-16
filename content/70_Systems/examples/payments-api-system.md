---
id: payments-api-system
type: system
title: Payments API
status: approved
owner: Payments Team
owner_team: Payments Engineering
runtime: Kubernetes / Go 1.21
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - system
  - api
  - payments
summary: >-
  Documents the Payments API service - its architecture, dependencies,
  runtime, and operational characteristics. USE A SYSTEM doc when you
  need to describe a RUNNING SERVICE or system as it exists today.
  System docs answer "what is this thing, how is it built, and what
  does it depend on?" They are the canonical source of truth for a
  service's architecture, repositories, runtime environment, and
  dependencies. Compare: a TDD designs what will be built; a System
  doc describes what IS built. A Runbook handles when the system
  breaks. A Guide teaches people how to work with the system.
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/payments-api
  - https://git.example.com/acme/payments-infrastructure
dependencies:
  - PostgreSQL 14 cluster (primary + 2 read replicas)
  - Redis 7 (caching and session management)
  - Authentication service (JWT validation)
  - Notification service (payment confirmation emails)
  - Stripe API (primary payment gateway)
  - PayPal API (secondary payment gateway)
runbooks:
  - service-outage-runbook
example: true
---

## Overview

The Payments API is the central service for all payment processing operations. It handles authorization, capture, refunds, and payment method storage for both internal services and partner integrations.

The service processes approximately 50,000 transactions per day with a peak of 200 TPS during business hours. It integrates with Stripe (primary) and PayPal (secondary) as payment gateways, with automatic failover between them.

## Architecture

The service follows a hexagonal (ports and adapters) architecture:

- **API Layer**: RESTful endpoints for payment operations (authorize, capture, refund, query). JWT-authenticated. Rate-limited to 100 req/s per client.
- **Domain Layer**: Payment processing workflows, validation rules, idempotency enforcement, and state machine transitions (pending → authorized → captured → settled, with refund branches).
- **Integration Layer**: Gateway adapters for Stripe and PayPal with circuit breaker pattern (5 failures in 30s triggers open state, 60s recovery window).
- **Data Layer**: PostgreSQL for transactional data with row-level locking on payment state transitions. Redis for caching payment method tokens and rate limiting counters.
- **Event Layer**: Publishes payment state change events to SQS for downstream consumers (invoicing, notifications, analytics).

## Repositories

- [payments-api](https://git.example.com/acme/payments-api) - Application code, migrations, Dockerfile
- [payments-infrastructure](https://git.example.com/acme/payments-infrastructure) - Terraform modules, Kubernetes manifests, monitoring dashboards

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones (us-east-1a, 1b, 1c)
- **Language**: Go 1.21 with standard library HTTP server
- **Replicas**: 4 pods minimum, autoscaling to 12 based on CPU (70%) and request rate (150 req/s per pod)
- **Resources**: 512Mi memory request / 1Gi limit, 250m CPU request / 1 CPU limit per pod
- **Deployment**: Blue-green via ArgoCD with health check gates
- **Configuration**: Environment variables via ConfigMaps, secrets via Kubernetes Secrets with 90-day rotation
- **TLS**: Terminated at the ingress controller, mTLS between services via service mesh

## Dependencies

- PostgreSQL 14 cluster (primary + 2 read replicas) - connection pool max 100, statement timeout 30s
- Redis 7 cluster - 3 nodes, maxmemory 2GB with allkeys-lru eviction
- Authentication service - JWT validation on every request, cached for token lifetime
- Notification service - async via SQS, non-blocking
- Stripe API - primary gateway, webhook receiver for async status updates
- PayPal API - fallback gateway, activated when Stripe circuit breaker opens

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime (max 43 minutes downtime/month) |
| Latency | P50 < 200ms, P95 < 500ms, P99 < 1s |
| Error rate | < 0.1% 5xx responses under normal conditions |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[example-service-outage-runbook|Service Outage (Payments API)]]
