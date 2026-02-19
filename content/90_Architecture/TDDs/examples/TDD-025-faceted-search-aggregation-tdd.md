---
id: TDD-025
type: tdd
title: Faceted Search Aggregation TDD
status: approved
owner: Tech Lead
created: '2024-11-12T15:17:14.465Z'
updated: '2026-11-12T00:47:12.270Z'
tags:
  - tdd
  - search-platform
summary: Faceted Search Aggregation TDD
related_adrs:
  - ADR-0018
  - ADR-0019
example: true
---

## Summary

Design the faceted search aggregation system that computes and returns facet counts alongside search results. Facets allow users to filter search results by structured dimensions (category, content type, date range, tags) and see the count of results per facet value. The implementation uses Elasticsearch aggregations as defined in [[ADR-0018|ADR-0018]] and must not degrade query latency beyond the thresholds established for hybrid search in [[ADR-0019|ADR-0019]].

## Overview

Faceted search adds a secondary query to each search request that computes document counts per facet dimension. The challenge is doing this efficiently: naively running large terms aggregations with thousands of buckets is expensive and was identified in REPORT-037 as the root cause of the queries-above-1-second problem.

Key design principles:
- **Post-filter aggregations**: Facet counts are computed against the unfiltered result set while results are filtered; this ensures counts remain stable as users apply filters
- **Circuit breaker for aggregations**: Requests with excessive bucket counts are rejected at the query layer before reaching Elasticsearch
- **Configurable aggregations**: Facet dimensions are configured in DynamoDB, not hardcoded; new facets can be added without code changes

## Architecture

- **Facet Config Loader**: Reads the list of active facet dimensions from DynamoDB `search-query-config`. Each dimension specifies: field name, aggregation type (`terms`, `date_histogram`, `range`), max bucket count, and display label.
- **Facet Query Builder**: Extends the Query DSL builder to add `aggs` clauses for each active facet dimension. Uses `post_filter` for active filter application so that facet counts reflect the full result set.
- **Bucket Size Guard**: Validates that the sum of requested bucket sizes across all facets does not exceed 500 total buckets. Requests exceeding this limit are rejected with a 400 error and an explanatory message.
- **Facet Response Formatter**: Transforms Elasticsearch aggregation response into a flat facet structure with label, value, count, and `is_selected` flag for each bucket.
- **Cache Layer**: Post-filter facet aggregations for high-frequency queries are cached in Redis for 60 seconds; cache key is `facets:{query_hash}:{active_filters_hash}`.

## Information Model

- **FacetConfig** (DynamoDB): `{ facet_id: string, field: string, agg_type: 'terms'|'date_histogram'|'range', max_buckets: int, label: string, enabled: bool }`
- **FacetBucket**: `{ value: string, count: number, is_selected: boolean }`
- **FacetGroup**: `{ facet_id: string, label: string, buckets: FacetBucket[] }`
- **FacetedSearchResponse**: `{ results: SearchHit[], total: number, facets: FacetGroup[], applied_filters: Record<string, string[]> }`

## Interfaces

- `GET /v1/search?q={query}&facets={facet_ids}&filter[category]={value}` — extended search endpoint with facet support
- `FacetQueryBuilder.buildAggregations(facets: FacetConfig[], activeFilters: Record<string, string[]>): Record<string, AggClause>` — builds `aggs` section
- `BucketSizeGuard.validate(facets: FacetConfig[], requestedSizes: Record<string, int>): ValidationResult`
- `FacetResponseFormatter.format(aggsResponse: ElasticsearchAggs, activeFilters: Record<string, string[]>): FacetGroup[]`
- `FacetCache.get(queryHash: string, filtersHash: string): FacetGroup[] | null`

## Files and Layout

```
src/
  facets/
    config-loader.ts      - DynamoDB facet config loading
    query-builder.ts      - Aggs clause construction with post_filter
    bucket-guard.ts       - Bucket size validation and circuit breaker
    response-formatter.ts - Elasticsearch aggs → FacetGroup transformation
    cache.ts              - Redis 60-second facet cache
  handler.ts              - Updated search Lambda (facets integration)
tests/
  facets/
    query-builder.test.ts
    bucket-guard.test.ts
    response-formatter.test.ts
    integration/
      faceted-search.test.ts
```

## Work Plan

1. **Phase 1 (Week 1)**: FacetConfig schema and DynamoDB loader; unit tests for config loading and caching
2. **Phase 2 (Week 2)**: FacetQueryBuilder with `post_filter` support; BucketSizeGuard validation logic
3. **Phase 3 (Week 3)**: FacetResponseFormatter; integration test against staging Elasticsearch
4. **Phase 4 (Week 4)**: Redis cache layer; load test at 800 QPS with facets enabled to validate P95 latency
5. **Phase 5 (Week 5)**: Production rollout with feature flag; monitor coordinator node CPU and latency

## Risks and Mitigations

- **Risk**: Large terms aggregations on high-cardinality fields (e.g., `author`) exhaust coordinating node memory. **Mitigation**: BucketSizeGuard enforces per-facet and total bucket limits; high-cardinality fields require explicit opt-in in facet config.
- **Risk**: Facet cache invalidation is too aggressive, defeating the cache benefit. **Mitigation**: Cache TTL is 60 seconds; facets do not change frequently enough for this to be a meaningful consistency issue.
- **Risk**: `post_filter` pattern unfamiliar to new engineers, leading to incorrect filter implementations. **Mitigation**: Document the pattern clearly in the TDD and code; add integration tests that verify facet counts are stable when filters are applied.
