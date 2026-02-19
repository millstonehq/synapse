---
id: SYSTEM-042
type: system
title: Customer API Gateway
status: approved
owner: Customer Engineering
owner_team: Customer Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2025-01-13T16:06:51.756Z'
updated: '2026-10-19T07:25:11.686Z'
tags:
  - system
  - customer-portal
summary: Customer API Gateway
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/customer-api-gateway
dependencies:
  - Customer Support Widget Service
  - Customer Portal Web Application
runbooks:
  - RUNBOOK-060
  - RUNBOOK-062
example: true
---

## Overview

The Customer API Gateway is the single entry point for all client-to-backend API traffic in the Customer Portal. It provides a unified GraphQL API surface that aggregates data from the Customer Support Widget Service, the Customer Portal Web Application, and downstream preference and analytics services. All external API calls from the portal front-end pass through this gateway.

The gateway enforces authentication, rate limiting, request validation, and field-level authorization. It targets 99.95% monthly uptime and is built on Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13.

## Architecture

- **GraphQL Layer**: Schema-stitched API combining types from multiple backend services. Persisted queries supported for production traffic to reduce payload size.
- **Auth Middleware**: JWT validation on every request. Tokens issued by the Identity service. Scopes are checked per resolver.
- **Rate Limiting**: Per-account token-bucket rate limiter (1000 req/min default, configurable per tier). Limits stored in Redis.
- **Routing Layer**: Resolvers call downstream REST or gRPC services. Connection pooling per downstream with circuit breaker protection (5 failures in 30s opens the circuit).
- **Observability**: Distributed tracing via OpenTelemetry. All resolver errors logged with correlation IDs for debugging.

## Repositories

- [customer-api-gateway](https://git.example.com/acme/customer-api-gateway) - Gateway code, schema definitions, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
- **Replicas**: 4 pods minimum, autoscaling to 10 on CPU (70%)
- **Deployment**: Blue-green via ArgoCD
- **TLS**: mTLS between gateway and downstream services

## Dependencies

- Customer Support Widget Service - support ticket data, chat session status
- Customer Portal Web Application - session context, feature flag state
- Redis - rate limit counters, response cache (TTL 60s for non-personalized data)

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| P95 GraphQL response | < 300ms |
| Error rate | < 0.2% 5xx responses |
| Recovery | MTTR < 20 minutes for SEV-1 |

## Runbooks

- [[RUNBOOK-079|Customer Portal SSL Certificate Runbook]]
