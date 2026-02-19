---
id: SYSTEM-004
type: system
title: Fraud Detection Service
status: approved
owner: Payment Engineering
owner_team: Payment Engineering
runtime: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
created: '2025-10-31T14:39:00.946Z'
updated: '2025-05-08T07:24:36.503Z'
tags:
  - system
  - payment-processing
summary: Fraud Detection Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/fraud-detection-service
dependencies:
  - Transaction Ledger Service
  - Payment Gateway Service
runbooks:
  - RUNBOOK-001
  - RUNBOOK-071
example: true
---

## Overview

The Fraud Detection Service evaluates every incoming payment authorization request in real time and returns a risk score and recommendation (allow / review / block) before the transaction is forwarded to the payment gateway. It applies a combination of rule-based checks and velocity signals to identify high-risk transactions.

The service is called synchronously on the hot path of payment authorization, so latency is critical. It targets a P99 response time of under 50ms to avoid adding meaningful overhead to the end-to-end payment flow.

## Architecture

- **Scoring API**: gRPC endpoint `/fraud.v1.FraudService/Evaluate` accepts payment context and returns a `RiskScore` (0–100) and `Decision` enum. Called by the Transaction Ledger Service on every authorization.
- **Rules Engine**: Stateless rule evaluation layer. Rules are loaded from PostgreSQL at startup and hot-reloaded every 60 seconds without restart.
- **Velocity Store**: Redis-backed counters for per-customer and per-card transaction frequency within sliding 1-minute, 1-hour, and 24-hour windows.
- **Event Consumer**: Subscribes to the SQS `payment-state-changes` topic to update historical fraud outcome data asynchronously.

## Repositories

- [fraud-detection-service](https://git.example.com/acme/fraud-detection-service) - Application code, rule definitions, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: Go 1.22
- **Replicas**: 4 pods minimum, autoscaling to 16 based on request rate
- **Resources**: 256Mi memory request / 512Mi limit per pod (rules held in-process)
- **Deployment**: Blue-green via ArgoCD
- **Protocol**: gRPC with mTLS

## Dependencies

- PostgreSQL 15 - rule definitions and fraud outcome history (read-heavy)
- Redis 7 - velocity counters with sub-millisecond read/write
- Transaction Ledger Service - upstream caller (synchronous on auth path)
- Payment Gateway Service - upstream caller for enrichment

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Latency | P50 < 10ms, P95 < 30ms, P99 < 50ms |
| False positive rate | < 0.5% of legitimate transactions blocked |
| Recovery | MTTR < 15 minutes for SEV-1 incidents |

## Runbooks

- See RUNBOOK-001 and RUNBOOK-071 for incident response procedures.
