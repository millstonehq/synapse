---
id: SYSTEM-011
type: system
title: Inventory Tracking Service
status: approved
owner: Inventory Engineering
owner_team: Inventory Engineering
runtime: Kubernetes / Go 1.22 / ClickHouse / Kafka
created: '2025-08-18T02:43:14.667Z'
updated: '2025-06-15T04:22:07.165Z'
tags:
  - system
  - inventory-management
summary: Inventory Tracking Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/inventory-tracking-service
dependencies:
  - SKU Registry Service
  - Warehouse Sync Gateway
runbooks:
  - RUNBOOK-017
  - RUNBOOK-021
example: true
---

## Overview

The Inventory Tracking Service is the authoritative system of record for stock quantities across all warehouse locations. It ingests stock movement events from warehouse management systems and supplier feeds, maintains per-SKU per-warehouse on-hand and available quantity records, and exposes a REST API consumed by order management, replenishment, and analytics systems.

The service processes approximately 800,000 stock movement events per day across 11 active warehouses, with a peak of 2,500 events per second during nightly batch sync windows. It serves around 400,000 inventory read requests per day from downstream consumers, with an availability SLA of 99.95% monthly uptime.

## Architecture

The service is organized into four layers. The ingest layer receives warehouse domain events from the Kafka `inventory.warehouse-events` topic, validates each event against the registered schema version, and writes immutable movement records to ClickHouse. The state layer maintains materialized views in ClickHouse representing current on-hand, reserved, and available quantities per SKU per warehouse, updated on every committed movement record.

The API layer exposes a versioned REST API for synchronous quantity queries. High-demand SKUs (those with more than 100 reservations per day) are served from a Redis read-through cache with sub-100ms freshness, while the remaining catalog is served directly from ClickHouse with up to 5-minute freshness. The event publication layer publishes outbound domain events to the `inventory.stock-movements` and `inventory.alerts` Kafka topics for downstream consumers including order management and the replenishment service.

## Repositories

- [inventory-tracking-service](https://git.example.com/acme/inventory-tracking-service) — application code, ClickHouse migrations, Kafka consumer configuration, Dockerfile
- [inventory-infrastructure](https://git.example.com/acme/inventory-infrastructure) — Terraform modules, Kubernetes manifests, Grafana dashboard definitions

## Runtime Environment

The service runs on Kubernetes across three availability zones (us-east-1a, 1b, 1c) with a minimum of 4 API pods and 2 event processor pods, autoscaling to 20 API pods and 8 processor pods based on request rate and Kafka consumer lag respectively. The Go 1.22 runtime is used for the API and event processor components. ClickHouse 23.8 provides the primary data store, running as a 3-node cluster with synchronous replication. Redis 7 (3-node cluster, 4GB per node) serves the high-demand SKU cache. All secrets are managed via Kubernetes Secrets with 90-day rotation enforced by the secrets management platform.

## Dependencies

- ClickHouse 23.8 cluster (3 nodes, synchronous replication) — primary inventory data store; connection pool max 50 per service instance
- Redis 7 cluster (3 nodes, 12GB total) — high-demand SKU read-through cache with allkeys-lru eviction
- Kafka cluster — consumes from `inventory.warehouse-events`; produces to `inventory.stock-movements` and `inventory.alerts`
- SKU Registry Service — validates SKU identifiers on event ingest; cached with 10-minute TTL
- Warehouse Sync Gateway — manages WMS adapter connections and routes warehouse events to the Kafka ingest topic
- Authentication service — JWT validation for all API requests, cached for token lifetime
