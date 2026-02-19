---
id: TDD-013
type: tdd
title: SKU Search and Discovery TDD
status: approved
owner: Principal Engineer
created: '2025-03-22T13:06:42.702Z'
updated: '2026-02-11T16:50:05.484Z'
tags:
  - tdd
  - inventory-management
summary: SKU Search and Discovery TDD
related_adrs:
  - ADR-0010
  - ADR-0013
example: true
---

## Summary

Design the SKU search and discovery capability for the inventory platform, enabling merchants, warehouse operators, and internal services to find SKUs by name, barcode, supplier code, category, and attribute combinations. As the SKU catalog approaches 1M records, PostgreSQL full-text search on a single table is insufficient; this design introduces a dedicated search index that scales independently from the transactional SKU registry. This work supports the read-model separation principle in [[ADR-0013|ADR-0013]].

## Overview

- **Dedicated search index**: SKU search is offloaded from PostgreSQL to Elasticsearch, which provides full-text search, faceted filtering, and fuzzy matching at scale.
- **Near-real-time sync**: SKU creates and updates in the PostgreSQL registry are propagated to Elasticsearch within 30 seconds via an event-driven sync pipeline.
- **Barcode fast path**: High-frequency barcode-to-SKU resolution (used by warehouse scanners) continues to use the Redis cache for sub-5ms latency, bypassing Elasticsearch entirely.
- **Backward-compatible API**: Existing SKU lookup endpoints are unchanged; search endpoints are new additions.

## Architecture

- **PostgreSQL SKU Registry**: Source of truth. Unchanged. SKU creates/updates publish lifecycle events.
- **Elasticsearch Index**: `sku-index` with mappings for name (analyzed), barcode (keyword), supplier_sku_code (keyword), category (keyword facet), attributes (nested). Populated from SKU lifecycle events.
- **Sync Worker**: Consumes SKU lifecycle events and writes to Elasticsearch. Handles retries and tracks sync lag via a checkpoint store.
- **Search API**: New HTTP endpoints for full-text search, category browse, and faceted filtering.
- **Barcode Resolution API**: Unchanged endpoint; Redis cache remains the primary path with PostgreSQL fallback.

## Information Model

- **SKU (registry)**: `sku_id`, `name`, `description`, `supplier_id`, `supplier_sku_code`, `category_id`, `barcode` (EAN/UPC/GTIN), `unit_of_measure`, `dimensions`, `status`, `created_at`, `updated_at`
- **SKU (search index)**: Same fields plus `category_path` (hierarchical facet), `supplier_name` (denormalized), `search_keywords` (composite analyzed field)
- **SKULifecycleEvent**: `event_type` (created|updated|deprecated), `sku_id`, `changed_fields`, `occurred_at`

## Interfaces

- `GET /v1/skus/search?q={query}&category={id}&supplier={id}&page={n}` - Full-text SKU search with faceting
- `GET /v1/skus/browse/category/{category_id}` - Category-level SKU browse with pagination
- `GET /v1/skus/barcode/{barcode}` - Barcode resolution (existing; Redis cache path)
- `GET /v1/skus/{sku_id}` - Single SKU lookup (existing; PostgreSQL)
- Internal: `PUT /internal/search-index/{sku_id}` - Sync worker writes SKU to Elasticsearch index

## Files and Layout

```
cmd/search-api/main.go        - Search API entry point
cmd/sync-worker/main.go       - SKU lifecycle event consumer
internal/
  search/                     - Elasticsearch client, index management, query builders
  sync/                       - Lifecycle event consumer, checkpoint tracking
  barcode/                    - Barcode resolution (Redis + PostgreSQL fallback)
  handler/                    - HTTP handlers for search and browse endpoints
  model/                      - SKU domain model, index document mapping
infra/
  elasticsearch.tf             - Elasticsearch domain definition
  index-mapping.json           - SKU index field mappings
```

## Work Plan

1. **Phase 1 - Elasticsearch cluster and index design (Week 1-2)**: Provision cluster, define index mapping, test full-text and facet queries at 1M document scale
2. **Phase 2 - Sync pipeline (Week 3-4)**: SKU lifecycle event publisher, sync worker, checkpoint tracking, initial full-catalog backfill
3. **Phase 3 - Search API (Week 5-6)**: Search and browse endpoints, pagination, faceted filtering, relevance tuning
4. **Phase 4 - Barcode optimization (Week 7)**: Cache warm-up improvements, predictive prefetch for high-frequency barcodes
5. **Phase 5 - Cutover and load test (Week 8)**: Route search traffic to new service; validate P95 latency at 2x peak query volume

## Risks and Mitigations

- **Risk: Elasticsearch sync lag exceeds 30-second SLA during high SKU creation bursts**: Mitigation: Buffer sync events in RabbitMQ with dedicated high-priority queue; scale sync workers horizontally
- **Risk: Relevance tuning produces poor search results for short product names**: Mitigation: A/B test search ranking with a sample of internal users before production rollout; instrument click-through rates
- **Risk: Elasticsearch cluster cost exceeds budget**: Mitigation: Start with 3-node cluster (2 data, 1 master); right-size after observing real query patterns at 30 days
