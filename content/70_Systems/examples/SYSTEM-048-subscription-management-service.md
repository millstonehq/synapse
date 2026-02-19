---
id: SYSTEM-048
type: system
title: Subscription Management Service
status: draft
owner: Billing Engineering
owner_team: Billing Engineering
runtime: Kubernetes / Go 1.22 / ClickHouse / Kafka
created: '2025-04-21T01:39:00.618Z'
updated: '2026-10-10T04:00:41.174Z'
tags:
  - system
  - billing-engine
summary: Subscription Management Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/subscription-management-service
dependencies:
  - Usage Metering Service
  - Invoice Generation Service
runbooks:
  - RUNBOOK-080
  - RUNBOOK-065
example: true
---

## Overview

The Subscription Management Service owns the lifecycle of customer subscriptions within the Billing Engine. It manages plan assignments, renewal scheduling, upgrade and downgrade workflows, and cancellation processing. The service is the source of truth for subscription state and publishes state change events to the Billing Event Processor for downstream billing actions.

The service handles approximately 15,000 subscription state transitions per day, with peak load at month-end renewal windows. It consumes usage aggregates from the Usage Metering Service and triggers invoice generation via the Invoice Generation Service at the end of each billing period.

## Architecture

- **Subscription API**: REST endpoints for CRUD operations on subscriptions, plan changes, and cancellations. Authenticated via JWT. Rate-limited per tenant.
- **State Machine Engine**: Go 1.22 implementation of the subscription state machine (trial → active → past_due → cancelled, with upgrade/downgrade branches). Uses optimistic locking on ClickHouse rows for concurrent transition safety.
- **Renewal Scheduler**: Kafka consumer group that processes scheduled renewal events. Idempotent by design — duplicate events produce no side effects.
- **Plan Management**: Manages pricing plan definitions and entitlement mappings. Plans are versioned; customers retain their plan version until they explicitly change.
- **Event Publishing**: Publishes `subscription.state_changed` and `subscription.renewed` events to Kafka for the Billing Event Processor.

## Repositories

- [subscription-management-service](https://git.example.com/acme/subscription-management-service) - Application code, Kafka consumers, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Go 1.22 / ClickHouse / Kafka
- **Replicas**: 3 pods minimum (API), 2 pods (renewal workers), autoscaling to 10 at month-end
- **Resources**: 512Mi memory request / 1Gi limit, 250m CPU request / 1 CPU limit per pod
- **Deployment**: Blue-green via ArgoCD
- **Configuration**: Environment variables via ConfigMaps, secrets via Kubernetes Secrets

## Dependencies

- ClickHouse cluster - subscription state and plan version storage
- Kafka 3.x cluster - event bus for renewal scheduling and state change publishing
- Usage Metering Service - queries aggregated usage at billing period close
- Invoice Generation Service - triggered to generate invoices at renewal

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| API latency | P95 < 300ms |
| Renewal processing lag | < 2 minutes after billing period close |
| Error rate | < 0.1% state transition failures |

## Runbooks

- [[RUNBOOK-080|Billing Proration Calculation Error]]
- [[RUNBOOK-065|Subscription Renewal Processing Lag]]
