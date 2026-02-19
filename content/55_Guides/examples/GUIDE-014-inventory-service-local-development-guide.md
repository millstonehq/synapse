---
id: GUIDE-014
type: guide
title: Inventory Service Local Development Guide
status: approved
owner: Developer Experience
created: '2025-09-25T10:20:26.771Z'
updated: '2025-11-23T15:15:25.167Z'
tags:
  - guide
  - inventory-management
summary: Inventory Service Local Development Guide
audience: internal
related_systems:
  - SYSTEM-014
  - SYSTEM-015
related_sops:
  - SOP-027
  - SOP-021
example: true
---

## Why This Matters

The inventory service is a high-throughput, event-driven system that interacts with Kafka, ClickHouse, and multiple warehouse APIs. Getting your local development environment right from the start saves hours of debugging integration issues and ensures that changes you make locally will behave predictably when deployed to production.

This guide covers everything you need to run the inventory service locally with realistic data, send and receive events, and validate your changes before opening a PR.

## Prerequisites

Before starting, ensure you have the following installed and configured:

- Docker Desktop (version 24 or later) — required for running Kafka, ClickHouse, and Redis locally
- Go 1.22 or later — the inventory service is written in Go
- `kubectl` configured for the staging cluster — for inspecting staging data when needed
- Access to the internal container registry — run `docker login registry.example.com` with your SSO credentials
- The repository cloned: `git clone https://git.example.com/acme/inventory-tracking-service`

## Setting Up Your Local Environment

The inventory service uses Docker Compose to orchestrate all local dependencies. From the repository root, run:

```bash
cp .env.example .env.local
docker compose -f docker-compose.dev.yml up -d
go run ./cmd/server
```

The `.env.example` file contains all required configuration with safe local defaults. The `docker-compose.dev.yml` file starts Kafka (with a UI available at `localhost:8080`), ClickHouse, Redis, and a mock warehouse API that simulates event delivery.

To seed the local ClickHouse database with realistic SKU and warehouse data, run the seed script:

```bash
go run ./cmd/seed --warehouses=3 --skus=1000
```

This creates 3 local warehouses and 1,000 SKUs with randomized stock levels.

## Working with Inventory Events Locally

The local Kafka instance is pre-configured with the same topic names used in production. To send a test stock movement event, use the event generator tool:

```bash
go run ./cmd/eventgen --type=stock.adjusted --sku=ELEC-ACME-HDPH200-BLK --warehouse=WH001 --delta=50
```

You can watch events flowing through the system in the Kafka UI at `localhost:8080`. The inventory service will consume and process the event, updating the ClickHouse stock record. Verify the result:

```bash
curl localhost:8090/v1/inventory?sku_id=ELEC-ACME-HDPH200-BLK&warehouse_id=WH001
```

## Running Tests

The test suite is split into unit tests (no external dependencies) and integration tests (requires the Docker Compose stack running):

```bash
# Unit tests only — fast, no Docker required
go test ./... -short

# Integration tests — requires Docker Compose stack
go test ./... -tags=integration
```

Always run the full integration test suite before pushing. The CI pipeline will block merges if integration tests fail.

## Common Questions

**"The Kafka consumer isn't processing my test events."** Check that the consumer group offset hasn't advanced past your test messages. If you sent events before starting the server, reset the consumer group offset: `kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group inventory-events-processor --reset-offsets --to-earliest --execute --topic inventory.events`.

**"ClickHouse queries are returning stale data."** ClickHouse uses eventual consistency for some table engines. In local development, force a merge: `OPTIMIZE TABLE inventory.stock_movements FINAL`.
