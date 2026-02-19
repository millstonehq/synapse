---
id: SYSTEM-012
type: system
title: Warehouse Sync Gateway
status: deprecated
owner: Inventory Engineering
owner_team: Inventory Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-07-12T22:53:28.588Z'
updated: '2026-07-19T19:48:13.337Z'
tags:
  - system
  - inventory-management
summary: Warehouse Sync Gateway
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/warehouse-sync-gateway
dependencies:
  - Inventory Event Bus
  - Inventory Tracking Service
runbooks:
  - RUNBOOK-021
  - RUNBOOK-018
example: true
---

## Overview

The Warehouse Sync Gateway is the integration layer responsible for bidirectional synchronization of stock data between the internal inventory platform and external warehouse management systems (WMS). It normalizes data formats across multiple WMS providers and ensures that stock movements recorded in third-party warehouses are reflected in the platform's authoritative inventory records.

The gateway processes approximately 20,000 sync events per day across 12 active warehouse connections, handling goods receipts, pick confirmations, cycle count reconciliations, and location transfers. It publishes normalized events downstream to the Inventory Event Bus for consumption by the Stock Level Calculator and other subscribers.

## Architecture

The gateway uses an adapter-per-warehouse pattern to isolate provider-specific protocol details:

- **Inbound Adapter Layer**: Receives webhook notifications or polls warehouse APIs on a configurable schedule. Each warehouse has a dedicated adapter implementing a common `WarehouseSyncAdapter` interface.
- **Normalization Layer**: Translates warehouse-native event formats (EDI 846, proprietary JSON, XML) into the internal `StockEvent` schema. Idempotency is enforced using the warehouse's native transaction ID.
- **Outbound Publisher**: Publishes normalized `StockEvent` messages to the Inventory Event Bus. Failed publishes are retried with exponential backoff up to 3 attempts, then dead-lettered.
- **Reconciliation Job**: A nightly Lambda function compares warehouse-reported stock levels against the platform's current totals and raises discrepancy alerts when variance exceeds configurable thresholds.

## Repositories

- [warehouse-sync-gateway](https://git.example.com/acme/warehouse-sync-gateway) - Application code, adapter implementations, Lambda functions

## Runtime Environment

- **Platform**: Lambda / Node.js 20 (event-driven adapters) with DynamoDB for idempotency tracking
- **Deployment**: Serverless Framework with per-warehouse function concurrency limits
- **Configuration**: SSM Parameter Store for warehouse credentials, rotating every 90 days
- **Invocation**: Event-driven (API Gateway webhooks) and scheduled (EventBridge cron for polling adapters)

## Dependencies

- Inventory Event Bus - downstream publisher for normalized stock events
- Inventory Tracking Service - source of truth for reconciliation comparisons
- DynamoDB - idempotency key store (TTL 7 days) and sync state tracking
- SSM Parameter Store - warehouse API credentials and connection config

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Sync latency | Webhook events processed within 30s of receipt |
| Reconciliation frequency | Nightly, completing before 06:00 UTC |
| Error rate | < 0.5% failed sync events under normal conditions |

## Runbooks

- [[RUNBOOK-021|Inventory Sync Outage Runbook]]
- [[RUNBOOK-018|Warehouse Gateway Degraded Runbook]]
