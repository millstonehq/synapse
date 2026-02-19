---
id: WIKI-023
type: wiki
title: Data Transformation - Pattern Library
status: deprecated
owner: Data Team
created: '2024-12-17T01:29:10.044Z'
updated: '2026-03-28T10:44:42.174Z'
tags:
  - wiki
  - data-pipeline
summary: Data Transformation - Pattern Library
source_repo: https://git.example.com/acme/data-transformation
commit_sha: 4e02dc3075cebaf0c984bbf0ed8aa835a68192b1
generated_at: '2026-10-23T23:51:50.620Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: high
example: true
---

## Overview

This page catalogs the reusable transformation patterns implemented across the data pipeline's dbt model library. Patterns are standardized SQL templates that solve common transformation problems consistently. Using a pattern from this library avoids reinventing solutions and ensures that quality, lineage, and performance characteristics are predictable across models.

The library currently contains 8 patterns covering the most common transformation needs. Each entry describes the problem, the standard implementation approach, and a concrete dbt example.

## Architecture

Pattern categories and their use in the model layers:

- **Staging layer patterns**: Applied in `models/staging/` to clean raw ingested records before any business logic is applied
- **Intermediate layer patterns**: Applied in `models/intermediate/` to join and denormalize data across source systems
- **Mart layer patterns**: Applied in `models/marts/` to produce analytics-ready fact and dimension tables

## Key Components

### Incremental Load Pattern

Used for tables where only new or updated records need to be processed on each run. Reduces transformation time by 60-80% compared to full refreshes for high-volume tables.

```sql
{{ config(materialized='incremental', unique_key='event_id') }}
SELECT * FROM {{ ref('stg_events') }}
{% if is_incremental() %}
WHERE ingested_at > (SELECT MAX(ingested_at) FROM {{ this }})
{% endif %}
```

### Type-2 Slowly Changing Dimension (SCD2) Pattern

Used to track historical changes to dimension records. Maintains `valid_from`, `valid_to`, and `is_current` columns. Implemented via dbt snapshots with the `timestamp` strategy.

### Surrogate Key Pattern

All dimension tables generate surrogate keys using `dbt_utils.generate_surrogate_key()` over the natural key fields. This decouples downstream joins from source system primary key formats.

### Deduplication Pattern

Used in staging models where the upstream Kafka topic may deliver duplicate events. Deduplication is applied using `ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_time DESC) = 1`.

## Configuration

Pattern defaults are documented in `dbt_project.yml`:

- `+materialized: table` — default for mart models
- `+materialized: incremental` — default for high-volume staging models
- `+on_schema_change: fail` — prevents silent column drops; requires explicit model update
- `+full_refresh: false` — prevents accidental full refreshes in production CI runs
