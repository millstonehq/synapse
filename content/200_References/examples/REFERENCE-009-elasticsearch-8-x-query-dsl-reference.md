---
id: REFERENCE-009
type: reference
title: Elasticsearch 8.x Query DSL Reference
status: published
owner: Security Team
created: '2025-04-30T20:59:52.142Z'
updated: '2026-07-20T22:55:11.251Z'
tags:
  - reference
  - search-platform
summary: Elasticsearch 8.x Query DSL Reference
upstream_url: https://docs.example.com/elasticsearch-8-x-query-dsl-reference
last_synced: '2026-04-01T22:40:36.817Z'
attribution: Cloud Native Computing Foundation
license: CC BY-SA 4.0
category: api-reference
example: true
---

## Overview

The Elasticsearch 8.x Query DSL is a JSON-based query language used to define search queries against an Elasticsearch cluster. Queries are composed of leaf query clauses (which match specific field values) and compound query clauses (which combine other clauses with boolean logic or scoring modifiers). This reference covers the query types and aggregations used by our Search Platform services.

All queries are sent to the cluster via the `_search` API against a read alias (e.g., `search-content-read`). Direct writes use the `_bulk` API against a write alias (e.g., `search-content-write`). Query DSL syntax is identical whether targeting Elasticsearch 8.x or OpenSearch 2.x for the constructs used in our stack.

## Full-Text Query Types

### multi_match

The primary full-text query type used by the Search Query Processing Service. Runs the same query string across multiple fields simultaneously.

```json
{
  "multi_match": {
    "query": "machine learning tutorials",
    "fields": ["title^3", "description^1.5", "tags^2", "body"],
    "type": "best_fields",
    "tie_breaker": 0.3,
    "minimum_should_match": "75%"
  }
}
```

Field boost multipliers (`^N`) amplify the BM25 score contribution from high-signal fields. `type: best_fields` uses the score of the best-matching field plus a fraction of other field scores via `tie_breaker`.

### match

Used for single-field queries and in integration tests.

```json
{
  "match": {
    "title": {
      "query": "search indexing",
      "operator": "and"
    }
  }
}
```

`operator: and` requires all query terms to appear in the field (higher precision, lower recall than the default `or`).

### match_phrase

Used for exact phrase matching in the navigational query path.

```json
{
  "match_phrase": {
    "title": {
      "query": "real-time indexing pipeline",
      "slop": 1
    }
  }
}
```

`slop` allows up to N transpositions between terms, accommodating minor word order variation.

## Vector and Hybrid Query Types

### knn (Approximate Nearest Neighbor)

Used for semantic similarity search. Requires a `dense_vector` field with `index: true` and `similarity: cosine`.

```json
{
  "knn": {
    "field": "content_vector",
    "query_vector": [0.012, -0.045, 0.231, ...],
    "k": 100,
    "num_candidates": 500
  }
}
```

`k` controls how many nearest neighbors are returned from the HNSW index. `num_candidates` sets the size of the internal candidate pool — higher values improve recall at the cost of latency. Our configuration uses `k=100, num_candidates=500` for the top-100 candidate retrieval step before re-ranking.

### Hybrid Query (bool + knn)

BM25 and vector results are retrieved in separate parallel requests, then merged using Reciprocal Rank Fusion in application code. Elasticsearch 8.x does not natively support RRF for this use case; the merge happens in the Search Query Processing Service.

```json
// Request 1: BM25
{ "query": { "multi_match": { ... } }, "size": 100 }

// Request 2: Vector (ANN)
{ "knn": { "field": "content_vector", ... }, "size": 100 }
```

## Filter and Boolean Queries

### bool

Combines multiple query clauses. Clauses in `must` contribute to the score; `filter` clauses are score-neutral (cached by Elasticsearch).

```json
{
  "bool": {
    "must": [
      { "multi_match": { "query": "search indexing", "fields": ["title^3", "body"] } }
    ],
    "filter": [
      { "term": { "status": "published" } },
      { "term": { "content_type": "documentation" } },
      { "range": { "published_at": { "gte": "now-1y" } } }
    ]
  }
}
```

Always place non-scoring constraints in `filter` rather than `must` to leverage Elasticsearch's filter cache and avoid polluting relevance scores.

### term / terms

Exact-value matching for keyword fields (not analyzed). Used for facet filters.

```json
{ "term": { "category.keyword": "Engineering" } }
{ "terms": { "tags.keyword": ["elasticsearch", "search"] } }
```

## Aggregations

### terms aggregation (facets)

Used by the faceted search feature to compute bucket counts per field value.

```json
{
  "aggs": {
    "by_content_type": {
      "terms": {
        "field": "content_type.keyword",
        "size": 10,
        "min_doc_count": 1
      }
    }
  }
}
```

Always use `post_filter` (not `query` filter) when combining facet counts with a user-selected facet filter so that counts for unselected facets reflect the unfiltered document set.

### date_histogram

Used in the analytics pipeline to bucket search events by time period.

```json
{
  "aggs": {
    "queries_per_hour": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "hour",
        "time_zone": "UTC"
      }
    }
  }
}
```

## Index Mapping Conventions

The following field naming and type conventions are enforced by our index templates:

| Field | Mapping | Notes |
|-------|---------|-------|
| `title` | `text` with `english` analyzer + `.keyword` sub-field | `.keyword` used for sorting and term aggregations |
| `body` | `text` with `english` analyzer, `index_options: offsets` | Offsets required for highlighting |
| `content_vector` | `dense_vector`, dims=1536, `index: true`, `similarity: cosine` | OpenAI text-embedding-3-small output dimension |
| `content_type` | `keyword` | Not analyzed; used for faceting and filtering |
| `tags` | `keyword` array + `.text` analyzed sub-field | `.text` sub-field included in multi_match queries |
| `published_at` | `date` | ISO 8601 format required |
| `document_id` | `keyword` | External document identifier; used as routing key |

## Sync Notes

This reference documents the Query DSL patterns used in our Search Platform as of Elasticsearch 8.12. Verify compatibility when upgrading to a new major version. The `knn` query syntax changed from Elasticsearch 8.0 to 8.4 (the nested `knn` key moved to the top level of the request body); our codebase uses the 8.4+ top-level syntax. For the full upstream Elasticsearch Query DSL documentation, see the upstream URL above.
