---
id: SYSTEM-002
type: system
title: Transaction Ledger Service
status: accepted
owner: Payment Engineering
owner_team: Payment Engineering
runtime: Kubernetes / TypeScript / PostgreSQL 16 / Redis 7
created: '2025-05-22T06:41:28.204Z'
updated: '2026-08-20T01:35:21.436Z'
tags:
  - system
  - payment-processing
summary: Transaction Ledger Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/transaction-ledger-service
dependencies:
  - Fraud Detection Service
  - Payment Gateway Service
runbooks:
  - RUNBOOK-071
  - RUNBOOK-004
example: true
---

## Overview

The Transaction Ledger Service is the authoritative source of truth for all payment transaction records within the payment processing platform. It maintains a complete, append-only event log of every state transition for every payment, enabling audit trails, reconciliation, and downstream event streaming.

The service handles approximately 50,000 transaction records per day, supporting both real-time writes from the payment gateway layer and batch reads from the reconciliation and reporting systems. It integrates with the Fraud Detection Service for enrichment and exposes a query API for downstream consumers.

## Architecture

The service is built around an event-sourced data model:

- **Write Path**: Accepts payment state change events from upstream services, validates idempotency, persists to the `payment_events` table, and publishes to SQS for downstream consumers.
- **Read Path**: Materialised views of current payment state derived from the event log. Supports filtering by customer, status, date range, and gateway reference.
- **Reconciliation Interface**: Exposes batch endpoints for the Payment Reconciliation Engine to pull settled transactions within a time window.
- **Data Layer**: PostgreSQL 16 with partitioned `payment_events` table (monthly partitions), row-level locking on state transitions. Redis 7 for idempotency key caching.

## Repositories

- [transaction-ledger-service](https://git.example.com/acme/transaction-ledger-service) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: TypeScript (Node.js 20)
- **Replicas**: 3 pods minimum, autoscaling to 10 based on CPU (70%)
- **Resources**: 512Mi memory request / 1Gi limit per pod
- **Deployment**: Blue-green via ArgoCD with health check gates
- **Configuration**: Environment variables via ConfigMaps, secrets via Kubernetes Secrets with 90-day rotation

## Dependencies

- PostgreSQL 16 cluster (primary + 2 read replicas) - connection pool max 80, statement timeout 30s
- Redis 7 cluster - idempotency key cache, TTL 7 days
- Fraud Detection Service - event enrichment via synchronous call on write path
- Payment Gateway Service - upstream event producer
- SQS - downstream event delivery to reconciliation and analytics consumers

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Write latency | P95 < 150ms |
| Read latency | P95 < 300ms |
| Error rate | < 0.1% 5xx responses |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-071|Payment Currency Conversion Failure Runbook]]
