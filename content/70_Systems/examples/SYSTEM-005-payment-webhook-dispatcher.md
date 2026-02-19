---
id: SYSTEM-005
type: system
title: Payment Webhook Dispatcher
status: approved
owner: Payment Engineering
owner_team: Payment Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2025-07-20T17:57:24.989Z'
updated: '2025-04-10T13:21:28.734Z'
tags:
  - system
  - payment-processing
summary: Payment Webhook Dispatcher
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/payment-webhook-dispatcher
dependencies:
  - Payment Gateway Service
  - Fraud Detection Service
runbooks:
  - RUNBOOK-001
  - RUNBOOK-007
example: true
---

## Overview

The Payment Webhook Dispatcher receives inbound webhook events from payment gateways (Stripe, PayPal) and fans them out to registered internal consumers. It handles HMAC signature verification, deduplication, ordered delivery, and retry logic so that downstream services receive a reliable stream of payment state change notifications.

The dispatcher processes both synchronous confirmations (e.g., `payment_intent.succeeded`) and asynchronous status updates (e.g., `charge.refunded`, `dispute.created`) from the gateway's webhook endpoints.

## Architecture

- **Inbound Receiver**: HTTP endpoint that accepts raw webhook payloads from gateways. Verifies HMAC signature before queuing. Returns 200 immediately to avoid gateway retries.
- **Deduplication Layer**: Checks webhook event ID against a Redis set with 24-hour TTL. Drops exact duplicates.
- **Dispatcher Queue**: SQS FIFO queue per gateway. Workers pull events and route to registered consumer endpoints by event type.
- **Retry Engine**: Exponential backoff with jitter (max 5 retries, 30-minute cap). Failed events after retries go to a dead-letter queue with alerting.
- **Consumer Registry**: PostgreSQL table of registered consumers with their endpoint URL, subscribed event types, and delivery status.

## Repositories

- [payment-webhook-dispatcher](https://git.example.com/acme/payment-webhook-dispatcher) - Application code, Dockerfile

## Runtime Environment

- **Platform**: ECS Fargate (long-running worker tasks)
- **Language**: Python 3.12
- **Tasks**: 2 minimum, autoscaling to 8 based on SQS queue depth
- **Storage**: OpenSearch for webhook event log and search, Redis 7 for deduplication

## Dependencies

- OpenSearch - event log, searchable by payment ID and event type
- Redis 7 - deduplication cache
- SQS FIFO queues - per-gateway event delivery
- Payment Gateway Service - webhook sender registration
- Fraud Detection Service - enrichment hook for `payment_intent.created` events

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Delivery latency | P95 < 5s from gateway receipt to consumer delivery |
| Delivery success rate | > 99.5% events delivered within 30 minutes |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- See RUNBOOK-001 and RUNBOOK-007 for webhook delivery failure procedures.
