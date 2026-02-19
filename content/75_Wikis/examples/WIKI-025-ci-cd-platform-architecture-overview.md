---
id: WIKI-025
type: wiki
title: CI/CD Platform - Architecture Overview
status: draft
owner: CI/CD Team
created: '2024-03-02T01:28:51.844Z'
updated: '2025-07-14T22:26:20.438Z'
tags:
  - wiki
  - ci-cd-platform
summary: CI/CD Platform - Architecture Overview
source_repo: https://git.example.com/acme/ci-cd-platform
commit_sha: 458f28fd4ef04761b2d03bebe198adf48eb8af97
generated_at: '2025-09-01T18:02:23.410Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: low
example: true
---

## Overview

The CI/CD platform is an internal developer platform that provides end-to-end tooling for building, testing, and deploying software across all engineering teams. It spans five core services: the Build Orchestration Service, CI Runner Fleet Manager, Artifact Registry, Deployment Controller, and Release Dashboard Service. Together they implement a trunk-based delivery model with GitOps deployments via ArgoCD.

The platform processes approximately 8,000 builds and 80 deployments per day at steady state, with capacity to scale to 5x during high-traffic periods such as release sprints or large refactors.

## Architecture

The platform follows an event-driven, loosely coupled architecture. Each service has a well-defined responsibility and communicates via async events for non-blocking operations and REST for synchronous requests.

```
Developer pushes code
  → GitHub webhook → Build Orchestration Service
  → Job queued → CI Runner Fleet Manager
  → Runners execute build and tests
  → Artifacts pushed → Artifact Registry
  → build.completed event → Deployment Controller
  → Approval gates evaluated → ArgoCD sync issued
  → Deployment events → Release Dashboard Service
```

Key architectural decisions:
- All artifacts are immutable and content-addressed; re-running a build at the same commit SHA reuses existing artifacts
- Deployment approval gates are configurable per environment and service
- The Deployment Controller owns rollback authority; automated rollback triggers if post-deploy health checks fail

## Key Components

- **Build Orchestration Service**: Receives build triggers, manages job queues, and coordinates job lifecycle with the runner fleet
- **CI Runner Fleet Manager**: Provisions and autoscales ephemeral runner instances; dispatches jobs to appropriately-tagged runners
- **Artifact Registry**: Stores and versions all build outputs; enforces promotion model (ci → staging → production)
- **Deployment Controller**: Orchestrates ArgoCD syncs, evaluates approval gates, triggers rollbacks, and maintains the deployment audit log
- **Release Dashboard Service**: Aggregates events from all upstream services into a real-time and historical view for engineers and product teams

## Configuration

Platform-level configuration is managed via Kubernetes ConfigMaps and AWS SSM Parameter Store. Key tunable settings:

- Runner autoscale thresholds (queue depth per runner, scale-down cooldown)
- Deployment approval gate configurations per service and environment
- Artifact retention policies by promotion stage
- Alert thresholds for build time regression and deploy failure rate

## Dependencies

| Service | External Dependencies |
|---------|----------------------|
| Build Orchestration | PostgreSQL 16, RabbitMQ 3.13 |
| CI Runner Fleet | PostgreSQL 16, RabbitMQ 3.13 |
| Artifact Registry | DynamoDB, S3 |
| Deployment Controller | OpenSearch, Redis 7, ArgoCD |
| Release Dashboard | PostgreSQL 15, Redis 7 |
