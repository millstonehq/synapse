---
id: WIKI-033
type: wiki
title: Customer Portal - Architecture Overview
status: review
owner: Customer Team
created: '2025-01-12T23:50:54.683Z'
updated: '2025-04-04T15:22:36.174Z'
tags:
  - wiki
  - customer-portal
summary: Customer Portal - Architecture Overview
source_repo: https://git.example.com/acme/customer-portal
commit_sha: 55cf2d3c99fb8c03e50d9ea1c8c7f25f2e6be549
generated_at: '2025-09-03T18:34:37.642Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: low
example: true
---

## Overview

The Customer Portal is a multi-tier web application built to give customers self-service access to account management, support, and analytics. It is composed of five primary services: the Customer Portal Web Application (front-end), the Customer API Gateway (GraphQL aggregation layer), the Customer Preference Service (personalization storage), the Customer Support Widget Service (embedded chat and tickets), and the Customer Analytics Service (behavioral event processing).

The architecture prioritizes separation of concerns between presentation and business logic. The web application never talks to backend databases directly; all data access is mediated by the API Gateway.

## Architecture

The portal follows a layered architecture:

- **Client Tier**: Next.js server-rendered pages with React client components. Static assets served via CDN. The support widget is embedded asynchronously via an iframe.
- **Gateway Tier**: Customer API Gateway exposes a unified GraphQL schema. Aggregates data from downstream services. Enforces auth, rate limiting, and field-level access control.
- **Service Tier**: Preference Service (REST/PostgreSQL), Support Widget Service (WebSocket/ClickHouse/Kafka), Analytics Service (event ingest/OpenSearch).
- **Data Tier**: Each service owns its own data store. No shared databases across service boundaries.
- **Event Bus**: RabbitMQ (preferences) and Kafka (analytics/widget events) carry asynchronous change notifications between services.

## Key Components

- **Customer Portal Web Application**: Next.js front-end, server-side rendering, session management via httpOnly JWT cookies
- **Customer API Gateway**: GraphQL schema stitching, JWT validation, per-account rate limiting (1000 req/min), circuit-breaker protected downstream calls
- **Customer Preference Service**: Typed preference namespaces (notifications, display, communications), Redis TTL cache, RabbitMQ event publishing on write
- **Customer Support Widget Service**: WebSocket chat sessions, ClickHouse-backed ticket storage, Kafka event consumption for proactive suggestions

## Configuration

- All services configured via Kubernetes ConfigMaps and Secrets
- Secrets rotated every 90 days via the secrets management pipeline
- Feature flags managed centrally and distributed to services via the API Gateway configuration endpoint

## Dependencies

| Service | Depends On |
|---------|-----------|
| Web Application | API Gateway, CDN |
| API Gateway | Preference Service, Support Widget Service |
| Preference Service | Customer Analytics Service, Redis, RabbitMQ |
| Support Widget Service | Customer Analytics Service, Redis, Kafka |
| Analytics Service | OpenSearch, Redis |
