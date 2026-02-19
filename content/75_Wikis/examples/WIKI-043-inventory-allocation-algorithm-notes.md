---
id: WIKI-043
type: wiki
title: Inventory Allocation - Algorithm Notes
status: approved
owner: Inventory Team
created: '2025-10-08T02:37:48.607Z'
updated: '2026-06-07T23:50:03.003Z'
tags:
  - wiki
  - inventory-management
summary: Inventory Allocation - Algorithm Notes
source_repo: https://git.example.com/acme/inventory-allocation
commit_sha: 55d73ca14e6a385f94f0197108d83722af6c7d35
generated_at: '2025-09-14T17:01:55.416Z'
source_files:
  - cmd/allocation/main.go
  - internal/allocator/allocator.go
  - internal/allocator/location_ranker.go
  - internal/allocator/split_strategy.go
  - internal/model/allocation.go
  - internal/repository/availability_repository.go
generator: deepwiki
model: gpt-4o
importance: medium
example: true
---

## Overview

The `inventory-allocation` repository implements the allocation engine that determines which warehouse location(s) to allocate inventory from when an order is placed. The engine runs as a synchronous service called by the order service during the checkout flow, and it must return an allocation decision within the 20ms P99 latency budget set by the reservation system.

The allocation result drives which location's reserved stock is decremented during the subsequent reservation call. Correct allocation decisions minimise unnecessary cross-warehouse transfers and reduce fulfilment costs by routing to the warehouse closest to the customer.

## Entry Point

`cmd/allocation/main.go` starts the allocation gRPC service using manual dependency injection. The startup sequence:

1. Load configuration from environment variables (location ranker weights, split strategy thresholds)
2. Initialise Redis client for availability pre-check (CQRS read model)
3. Initialise PostgreSQL client for fallback availability queries
4. Create `AvailabilityRepository` (Redis primary, PostgreSQL fallback)
5. Create `LocationRanker` with configured weighting strategy
6. Create `Allocator` with injected repository and ranker
7. Register gRPC handler and start server on `:9090`

## Key Packages

### `internal/allocator`

The core allocation logic. The `Allocator.Allocate(ctx, req)` method is the main entry point called for each order line item.

**Location Ranking (`location_ranker.go`)**: Scores each warehouse location that has sufficient available stock to fulfil the requested quantity. The default ranking strategy weights four factors:

| Factor | Default Weight | Description |
|--------|--------------|-------------|
| Distance score | 0.40 | Haversine distance from warehouse to customer delivery postcode zone, normalised 0-1 (1 = closest) |
| Availability score | 0.30 | Ratio of available quantity to requested quantity, capped at 1.0. Locations with 10x the requested quantity score identically to locations with exactly the requested quantity |
| Stock health score | 0.20 | Inverse of days-of-stock-remaining: locations with a higher velocity relative to stock score higher, biasing allocation toward faster-turning locations to reduce overstock concentration |
| Transfer cost score | 0.10 | Penalises locations that are currently low on stock relative to their reorder point, to avoid triggering reorders from locations near their threshold |

The weights are configurable per merchant via the merchant allocation preferences store. Merchants can increase the distance weight to optimise for delivery speed, or increase the stock health weight to prioritise clearing slow-moving stock.

**Split Strategy (`split_strategy.go`)**: If no single location can fulfil the full requested quantity, the split strategy determines whether to split the order across multiple locations or decline the allocation (returning "insufficient stock").

```go
type SplitStrategy interface {
    ShouldSplit(req AllocationRequest, candidates []LocationScore) bool
    Split(req AllocationRequest, candidates []LocationScore) []AllocationLine
}
```

Two implementations are available:

- `NoSplitStrategy`: Never splits. Returns "insufficient stock" if no single location can satisfy the full quantity. Used by merchants who cannot fulfil split orders due to carrier constraints.
- `GreedyFillStrategy`: Fills the requested quantity from the highest-ranked location first, then uses the next-ranked location for the remainder, and so on until the quantity is satisfied or locations are exhausted. Default for merchants with multi-warehouse setups.

### `internal/model`

Domain entities for allocation:

- `AllocationRequest`: `order_id`, `sku_id`, `merchant_id`, `requested_qty`, `customer_postcode_zone`, `allowed_location_ids[]`
- `AllocationLine`: `location_id`, `allocated_qty`
- `AllocationResult`: `order_id`, `lines[]`, `strategy_used`, `latency_ms`
- `LocationScore`: `location_id`, `available_qty`, `score`, `score_breakdown`

### `internal/repository`

`AvailabilityRepository` reads available quantities from the CQRS Redis read model. The Redis key format is `avail:{merchant_id}:{sku_id}:{location_id}` with a 10-second TTL.

If a key is missing or Redis is unavailable, the repository falls back to a direct PostgreSQL query against the `stock_levels` projection table. The fallback adds approximately 8-12ms to allocation latency, which still fits within the 20ms P99 budget under normal load.

## Allocation Flow

For a single-line order request:

1. Retrieve available quantities for the requested SKU across all warehouse locations the merchant is configured to allocate from
2. Filter to locations with `available_qty >= 1` (any positive availability)
3. For `GreedyFillStrategy`: also retain locations with partial availability (for split fulfilment)
4. Score each candidate location using `LocationRanker`
5. Sort candidates by descending score
6. Apply split strategy to determine allocation lines
7. Return `AllocationResult` with the chosen locations and quantities

For multi-line orders, the allocator runs the above for each line independently. Location affinity (preferring the same warehouse for all lines to minimise split shipments) is applied as a post-processing step: if the top-scoring location for the first line also has stock for other lines in the order, those lines are preferentially allocated to the same location even if a different location would have scored slightly higher independently.

## Configuration

All configuration is passed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RANKER_DISTANCE_WEIGHT` | `0.40` | Weight for distance score |
| `RANKER_AVAILABILITY_WEIGHT` | `0.30` | Weight for availability score |
| `RANKER_STOCK_HEALTH_WEIGHT` | `0.20` | Weight for stock health score |
| `RANKER_TRANSFER_COST_WEIGHT` | `0.10` | Weight for transfer cost penalty |
| `DEFAULT_SPLIT_STRATEGY` | `greedy_fill` | Default split strategy for new merchants |
| `MAX_SPLIT_LOCATIONS` | `3` | Maximum number of locations in a split allocation |
| `REDIS_AVAILABILITY_TIMEOUT_MS` | `5` | Redis read timeout before falling back to PostgreSQL |

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `google.golang.org/grpc` | v1.60.0 | gRPC server and client |
| `github.com/jackc/pgx/v5` | v5.5.1 | PostgreSQL fallback queries |
| `github.com/redis/go-redis/v9` | v9.3.0 | CQRS availability read model |
| `github.com/umahmood/haversine` | v1.0.1 | Distance calculation for location ranking |

## Generation Notes

Generated from commit `55d73ca` on the `main` branch. The generator analysed Go source files, extracted interface definitions, struct fields, and configuration constants to produce this overview. The weighting values and strategy names are sourced from the source code defaults at the commit listed above. Re-generate when the allocation algorithm is materially changed.
