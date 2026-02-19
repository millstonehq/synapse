---
id: SYSTEM-015
type: system
title: SKU Registry Service
status: draft
owner: Inventory Engineering
owner_team: Inventory Engineering
runtime: Kubernetes / Node.js 20 / PostgreSQL 16
created: '2024-06-20T20:09:28.503Z'
updated: '2026-04-26T07:19:54.760Z'
tags:
  - system
  - inventory-management
summary: SKU Registry Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/sku-registry-service
dependencies:
  - Inventory Tracking Service
  - Stock Level Calculator
runbooks:
  - RUNBOOK-020
  - RUNBOOK-015
example: true
---

## Overview

The SKU Registry Service is the system of record for product and SKU master data used across the inventory platform. It stores SKU identifiers, descriptions, units of measure, barcode mappings (EAN, UPC, GTIN), product dimensions, and supplier cross-references. All other inventory services resolve SKU identity through this registry to ensure consistency.

The service manages approximately 850,000 active SKUs and supports both real-time lookup via a REST API and bulk export for warehouse management system onboarding. SKU lifecycle events (creation, attribute updates, deprecation) are published for downstream consumers.

## Architecture

- **SKU API**: RESTful CRUD endpoints for SKU management. Supports single-record lookups by internal ID, EAN, UPC, or GTIN, and paginated list queries with filtering by category, supplier, and status.
- **Barcode Resolution**: A dedicated lookup path optimized for high-frequency barcode-to-SKU resolution during warehouse scanning operations. Responses are cached in Redis with a 60-second TTL.
- **Bulk Export**: Scheduled and on-demand CSV/JSON export of the full SKU catalog for WMS onboarding, supplier reconciliation, and analytics feeds.
- **Event Publisher**: Publishes SKU lifecycle events (created, updated, deprecated) to downstream consumers via the inventory event infrastructure.

## Repositories

- [sku-registry-service](https://git.example.com/acme/sku-registry-service) - Application code, migrations, export jobs

## Runtime Environment

- **Platform**: Kubernetes / Node.js 20 with PostgreSQL 16
- **Replicas**: 3 API pods minimum with a dedicated 2-pod pool for bulk export jobs
- **Deployment**: Rolling deployments; migrations run as pre-deploy jobs with tested rollback scripts

## Dependencies

- Inventory Tracking Service - consumes SKU data for tracking record creation
- Stock Level Calculator - resolves SKU identity for stock level projections
- PostgreSQL 16 - SKU master data store with full-text search index on name/description
- Redis - barcode resolution cache (TTL 60s)

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Lookup latency | P95 < 50ms for cached barcode resolution |
| Bulk export | Complete within 30 minutes for full catalog |
| Data accuracy | SKU attributes match source of record within 1 sync cycle |

## Runbooks

- [[RUNBOOK-020|SKU Registry Degradation Runbook]]
- [[RUNBOOK-015|SKU Sync Failure Runbook]]
