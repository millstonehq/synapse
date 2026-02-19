---
id: SYSTEM-001
type: system
title: Payment Gateway Service
status: approved
owner: Payment Engineering
owner_team: Payment Engineering
runtime: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache
created: '2025-08-15T16:10:29.731Z'
updated: '2026-06-16T04:43:48.287Z'
tags:
  - system
  - payment-processing
summary: Payment Gateway Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/payment-gateway-service
dependencies:
  - Fraud Detection Service
  - Payment Webhook Dispatcher
runbooks:
  - RUNBOOK-003
  - RUNBOOK-005
example: true
---

## Overview

The Payment Gateway Service is the central system responsible for all payment transaction processing on the platform. It handles the complete payment lifecycle: authorization, capture, void, refund, and chargeback notification processing. The service abstracts over multiple underlying payment gateway providers through a provider adapter pattern, allowing the platform to route transactions to the optimal gateway based on payment method, geography, and routing rules without changes to upstream callers.

The service processes approximately 1,200 transactions per second at peak and maintains a 99.9% monthly uptime SLA. It is the primary integration point for checkout flows, subscription billing, and refund processing, and it emits payment lifecycle events consumed by fulfillment, analytics, and reconciliation systems.

## Architecture

The Payment Gateway Service follows a hexagonal architecture with a clear separation between the payment domain core and external integrations. The API layer exposes a RESTful interface for payment operations and uses JWT authentication with per-merchant rate limiting enforced at the ingress layer.

The domain layer manages payment state machine transitions (created → processing → succeeded/failed), idempotency enforcement using a Redis-backed idempotency store, and fraud risk scoring orchestration. The gateway integration layer contains provider adapters for each supported payment gateway, each implementing a common interface with request normalization, response mapping, and error code translation. A circuit breaker pattern (5 failures per 30 seconds triggers open state) protects the domain layer from cascading failures when a gateway is degraded. Events are published to an SNS/SQS fan-out pipeline for downstream consumers including the reconciliation service, webhook dispatcher, and analytics pipeline.

## Repositories

- [payment-gateway-service](https://git.example.com/acme/payment-gateway-service) — Application code, database migrations, provider adapters, and Dockerfile
- [payment-gateway-infrastructure](https://git.example.com/acme/payment-gateway-infrastructure) — ECS task definitions, Aurora cluster Terraform, ElastiCache configuration, and ALB routing rules
- [payment-gateway-dashboards](https://git.example.com/acme/payment-gateway-dashboards) — Grafana dashboard definitions and CloudWatch alarm configurations

## Runtime Environment

The service runs on AWS ECS Fargate with tasks distributed across three availability zones (us-east-1a, us-east-1b, us-east-1c) for high availability. The application is written in Java 21 using Spring Boot, with GraalVM native compilation used in production to reduce cold start times.

Minimum running task count is 4, scaling to a maximum of 16 tasks based on P95 authorization latency exceeding 300ms. Each task is allocated 2 vCPU and 4GB memory. Deployments use a blue-green strategy with health check gates on the `/health` endpoint before traffic is shifted. Secrets are managed via AWS Secrets Manager with automatic rotation; the application fetches secrets at startup and caches them with a 5-minute TTL. TLS is terminated at the Application Load Balancer; mutual TLS is used for outbound gateway connections.

## Dependencies

- **Aurora PostgreSQL** (primary + 2 read replicas) — persistent store for the payment ledger, transaction state, and idempotency records; connection pool maximum of 150 with statement timeout of 30 seconds
- **ElastiCache Redis** (cluster mode, 3 shards) — idempotency key store, token lookup cache, and rate limiting counters; 10GB total capacity with allkeys-lru eviction policy
- **Fraud Detection Service** — synchronous pre-authorization fraud scoring via internal gRPC API; circuit breaker configured to fail open (allow transaction) on fraud service unavailability
- **Payment Webhook Dispatcher** — consumes payment lifecycle events from SQS and delivers webhooks to merchant endpoints; asynchronous, non-blocking from the payment gateway service perspective
- **AWS Secrets Manager** — stores gateway API keys, webhook signing secrets, and database credentials with quarterly automatic rotation
