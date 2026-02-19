---
id: REFERENCE-010
type: reference
title: OpenSearch API Compatibility Reference
status: published
owner: Platform Team
created: '2025-12-06T05:16:30.797Z'
updated: '2025-08-07T11:27:58.174Z'
tags:
  - reference
  - search-platform
summary: OpenSearch API Compatibility Reference
upstream_url: https://docs.example.com/opensearch-api-compatibility-reference
last_synced: '2026-10-26T17:46:11.340Z'
attribution: W3C
license: CC BY-SA 4.0
category: blog-post
example: true
---

## Overview

OpenSearch 2.x maintains broad API compatibility with Elasticsearch 7.10.x (the final Apache-licensed Elasticsearch release). This reference documents the compatibility surface, known divergences, and migration considerations relevant to our Search Platform, which uses Elasticsearch 8.x for production search and OpenSearch 2.x for analytics event storage (per ADR-0021).

All new clusters provisioned after July 2025 are OpenSearch. Existing Elasticsearch 8.x clusters for production search remain on Elasticsearch until the next scheduled cluster replacement cycle. Engineers should use this reference when writing code that must run against both cluster types.

## Compatible API Surface

The following APIs behave identically between Elasticsearch 8.x and OpenSearch 2.x for our use cases:

| API | Compatible | Notes |
|-----|-----------|-------|
| `GET /_search` | Yes | All query DSL constructs we use (multi_match, bool, term, range, terms agg, date_histogram) are compatible |
| `POST /_bulk` | Yes | Request/response format identical |
| `PUT /{index}/_mapping` | Yes | Field mapping types and parameters are compatible |
| `GET /{index}/_count` | Yes | |
| `POST /{index}/_update_by_query` | Yes | |
| `POST /{index}/_delete_by_query` | Yes | |
| `GET /_cat/indices` | Yes | Column names and output format are compatible |
| `PUT /{index}/_settings` | Yes | |
| Index templates (`PUT /_index_template/`) | Yes | Component template syntax is identical |
| Index aliases (`POST /_aliases`) | Yes | |

## Known Incompatibilities

### Vector Search (knn)

The `knn` query syntax differs between Elasticsearch 8.4+ and OpenSearch 2.x.

**Elasticsearch 8.4+ (top-level knn):**
```json
{
  "knn": {
    "field": "content_vector",
    "query_vector": [...],
    "k": 100,
    "num_candidates": 500
  },
  "size": 20
}
```

**OpenSearch 2.x (knn inside query):**
```json
{
  "query": {
    "knn": {
      "content_vector": {
        "vector": [...],
        "k": 100
      }
    }
  },
  "size": 20
}
```

Our Search Query Processing Service uses a cluster-type abstraction layer (`QueryBuilder`) that detects the target cluster type from configuration and generates the appropriate syntax. Do not write raw knn queries against a cluster without using `QueryBuilder`.

### Dense Vector Field Mapping

Elasticsearch 8.x uses `index: true` to enable HNSW indexing on a `dense_vector` field. OpenSearch 2.x uses a separate `knn_vector` field type with `method` configuration.

**Elasticsearch 8.x:**
```json
{
  "content_vector": {
    "type": "dense_vector",
    "dims": 1536,
    "index": true,
    "similarity": "cosine"
  }
}
```

**OpenSearch 2.x:**
```json
{
  "content_vector": {
    "type": "knn_vector",
    "dimension": 1536,
    "method": {
      "name": "hnsw",
      "space_type": "cosinesimil",
      "engine": "nmslib",
      "parameters": { "ef_construction": 128, "m": 16 }
    }
  }
}
```

Our analytics OpenSearch cluster does not use vector fields, so this incompatibility only affects any future migration of the production search index to OpenSearch.

### Security and Authentication

Elasticsearch 8.x requires TLS and enables security (authentication/authorization) by default. OpenSearch 2.x ships with the Security plugin but can be run without it (security disabled) in controlled environments.

Our OpenSearch analytics cluster runs with the Security plugin enabled using basic auth. IAM-based authentication (via the OpenSearch AWS managed service) is used for the production analytics cluster. Elasticsearch uses API key authentication for service-to-service calls.

### Index Lifecycle Management (ILM) vs. Index State Management (ISM)

Elasticsearch uses ILM policies; OpenSearch uses ISM policies. Both implement hot/warm/cold/delete tier transitions but use different API endpoints and policy syntax.

| Feature | Elasticsearch | OpenSearch |
|---------|--------------|-----------|
| Policy API | `PUT /_ilm/policy/{name}` | `PUT /_plugins/_ism/policies/{name}` |
| Attach to index | `index.lifecycle.name` setting | ISM template or direct policy attachment |
| Rollover | `rollover` action in ILM | `rollover` action in ISM (compatible) |
| Retention | `delete` action with `min_age` | `delete` action with `min_index_age` |

Our OpenSearch analytics cluster uses ISM to transition indices from hot to warm after 7 days and delete after 90 days. The ISM policy is defined in the `search-analytics-ism-policy` Terraform resource.

## Client Library Compatibility

The `@elastic/elasticsearch` Node.js client (version 8.x) is **not compatible** with OpenSearch 2.x. For OpenSearch clusters, use the `@opensearch-project/opensearch` client.

Our codebase uses a cluster client factory (`ClusterClientFactory`) that returns the appropriate client based on the `CLUSTER_TYPE` environment variable (`elasticsearch` or `opensearch`). Both clients expose an identical application-level interface defined in `ISearchClient`.

## Sync Notes

This reference was last synced against OpenSearch 2.13 and Elasticsearch 8.12. Verify compatibility notes when upgrading either cluster. The vector search incompatibility section should be reviewed if OpenSearch 2.x introduces Elasticsearch-compatible knn syntax in a future release (tracked upstream as opensearch-project/OpenSearch#6523).
