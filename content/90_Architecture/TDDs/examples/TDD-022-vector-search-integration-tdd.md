---
id: TDD-022
type: tdd
title: Vector Search Integration TDD
status: accepted
owner: Tech Lead
created: '2025-10-11T10:34:05.036Z'
updated: '2026-10-11T16:00:22.718Z'
tags:
  - tdd
  - search-platform
summary: Vector Search Integration TDD
related_adrs:
  - ADR-0020
  - ADR-0019
example: true
---

## Summary

Design the integration of dense vector search (k-nearest neighbor via HNSW) into the existing Search Platform, implementing the hybrid search approach decided in [[ADR-0019|ADR-0019]]. This TDD covers the embedding generation pipeline, vector index configuration, query-time embedding, and the Reciprocal Rank Fusion merger, using the index alias pattern from [[ADR-0020|ADR-0020]].

The integration adds vector fields to the existing search index and introduces a new embedding service client used by both the indexing pipeline and the query processing service.

## Overview

Vector search extends the existing keyword (BM25) search by adding a semantic similarity dimension. For each document, a dense embedding vector is generated from the document's text content and stored in a `content_vector` field in Elasticsearch. At query time, the user's query is embedded into the same vector space, and ANN search finds semantically similar documents. The two result sets (BM25 and ANN) are merged using Reciprocal Rank Fusion.

Key design principles:
- **Async embedding at index time**: Embeddings are generated in the indexing pipeline, not at query time, to avoid query latency impact from embedding API calls for documents
- **Inline embedding at query time**: Query embedding is generated inline in the Lambda with a 50ms circuit breaker
- **Fallback to keyword-only**: If the embedding service is unavailable or times out, the query falls back to keyword-only BM25 without user-visible error

## Architecture

- **Embedding Service Client**: Shared library used by both the indexing pipeline and query processing service. Wraps the OpenAI embeddings API, handles batching (max 32 texts per call), caches results in Redis by content hash, and implements circuit breaker (fallback to null if API unavailable).
- **Index Template Extension**: Adds `content_vector` field (`type: dense_vector`, `dims: 1536`, `index: true`, `similarity: cosine`) to the Elasticsearch index template.
- **Indexing Pipeline Extension**: Embedding Worker stage generates vectors for new and updated documents. Skips vector generation and logs a warning if the embedding service circuit breaker is open (document indexed without vector; will be backfilled when circuit closes).
- **Query Processing Extension**: After parsing the query AST, generates a query embedding inline. Executes both a BM25 `multi_match` query and a `knn` query in parallel. Merges results using RRF.
- **RRF Merger**: Implements `score(d) = Σ 1/(k + rank_i(d))` for each retrieval method. `k=60` default, configurable in DynamoDB.

## Information Model

- **DocumentVector**: `{ document_id: string, vector: number[1536], model_version: string, generated_at: ISO8601 }`
- **EmbeddingCacheKey**: `embedding:v1:<sha256(text)>` in Redis, TTL 7 days
- **Elasticsearch `content_vector` field**: `dense_vector` type, 1536 dimensions, HNSW index with `m=16, ef_construction=100`
- **VectorSearchResult**: `{ document_id: string, bm25_rank?: number, ann_rank?: number, rrf_score: number }`

## Interfaces

- `EmbeddingClient.embed(texts: string[]): Promise<number[][]>` — batch embedding with Redis cache
- `EmbeddingClient.embedSingle(text: string, timeoutMs: number): Promise<number[] | null>` — query-time embedding with timeout
- `HybridQueryBuilder.build(ast: ASTNode, queryVector: number[] | null): ElasticsearchQuery` — builds combined BM25+kNN query; falls back to BM25-only if `queryVector` is null
- `RRFMerger.merge(bm25Results: SearchHit[], annResults: SearchHit[], k: number): SearchHit[]`

## Files and Layout

```
packages/embedding-client/
  src/
    client.ts         - OpenAI API wrapper with batching and circuit breaker
    cache.ts          - Redis cache for embedding vectors
    index.ts          - Public interface
  tests/

packages/search-query-processing/
  src/
    hybrid/
      query-builder.ts  - BM25 + kNN query construction
      rrf-merger.ts     - Reciprocal Rank Fusion implementation
    index.ts            - Lambda handler (updated)

packages/search-indexing-pipeline/
  src/
    workers/
      embedding-worker.ts  - Embedding generation stage (updated)
    index-templates/
      content-v8.json      - ES index template with dense_vector field
```

## Work Plan

1. **Phase 1 (Week 1-2)**: Implement and test EmbeddingClient library; Redis cache integration; circuit breaker with keyword-only fallback
2. **Phase 2 (Week 3)**: Update Elasticsearch index template with `content_vector` field; deploy to staging; run backfill job on existing documents
3. **Phase 3 (Week 4)**: Implement HybridQueryBuilder and RRFMerger; unit and integration tests against staging cluster
4. **Phase 4 (Week 5)**: Deploy to production with feature flag at 0%; shadow mode (hybrid computed but not returned to users); compare offline relevance metrics
5. **Phase 5 (Week 6-7)**: Ramp feature flag from 5% → 25% → 100% with CTR monitoring at each step; promote to GA if CTR improves >= 2%

## Risks and Mitigations

- **Risk**: OpenAI embedding API outage stops all indexing. **Mitigation**: Circuit breaker in EmbeddingClient falls back to indexing without vectors; backfill job catches up after recovery.
- **Risk**: Dense vector field increases Elasticsearch storage beyond capacity. **Mitigation**: Monitor disk utilization closely during rollout; 3x storage budget increase budgeted in infrastructure capacity plan.
- **Risk**: RRF fusion deprioritizes highly relevant BM25 results on head queries. **Mitigation**: A/B test 5% of queries before full rollout; abort if head-query NDCG@10 regresses more than 0.5%.
