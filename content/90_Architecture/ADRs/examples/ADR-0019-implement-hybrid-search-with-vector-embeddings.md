---
id: ADR-0019
type: adr
title: Implement Hybrid Search with Vector Embeddings
status: approved
owner: Staff Engineer
created: '2024-07-23T21:48:12.893Z'
updated: '2026-12-20T20:31:54.690Z'
tags:
  - adr
  - search-platform
summary: Implement Hybrid Search with Vector Embeddings
example: true
supersedes: ADR-0021
---

## Context

The current keyword-based search (Elasticsearch BM25) has a zero-result rate of 4.2% and a tail-query CTR of 18.9%. Users searching for concepts, synonyms, or natural-language phrases often receive poor or no results because BM25 requires lexical overlap between the query and document. A proof-of-concept demonstrated that adding dense vector (semantic) search reduces the zero-result rate to 1.1% and improves tail-query CTR.

Two architectural approaches were evaluated: (1) pure vector search replacing BM25, and (2) hybrid search combining BM25 and vector search scores. We also needed to decide on the embedding model source: self-hosted (e.g., sentence-transformers on our own GPU infrastructure) or hosted API (e.g., OpenAI text-embedding-3-small).

The decision needed to balance relevance quality, operational complexity, cost, and time-to-production. The engineering team has no prior experience running GPU inference workloads.

## Decision

We will implement **hybrid search** combining BM25 and approximate nearest-neighbor (ANN) vector search using Elasticsearch 8.x's native HNSW implementation. Scores from the two retrieval methods will be merged using **Reciprocal Rank Fusion (RRF)** with a `k` parameter of 60.

For the embedding model, we will use **OpenAI text-embedding-3-small** via the hosted API for document and query embedding. Embeddings will be generated at index time (not query time for documents) and cached in Redis by document content hash. Query-time embedding will be performed inline in the Search Query Processing Service with a 50ms timeout budget.

## Consequences

**Positive:**
- Hybrid search preserves BM25 precision on head queries (which are already well-served) while adding semantic recall for tail queries
- RRF is a parameter-free fusion method that avoids the need to tune score normalization across BM25 and ANN
- OpenAI hosted embedding eliminates the need to operate GPU infrastructure; time-to-production is weeks rather than months
- Elasticsearch 8.x HNSW is production-proven and requires no additional infrastructure

**Negative:**
- Operational dependency on OpenAI API introduces a new external failure mode; requires a fallback to keyword-only mode
- Embedding cost at scale: $0.02 per million tokens. At current document volume, embedding all documents costs ~$400/month
- Dense vector fields increase Elasticsearch storage per document by approximately 3x
- Query latency budget must accommodate the additional ANN query execution (~15-30ms)

**Neutral:**
- The `k=60` RRF parameter is a common default; tuning to content-type-specific values is a future optimization
- OpenAI can be replaced with a self-hosted model later if costs or latency become unacceptable; the interface is abstracted behind an embedding service client

## Alternatives Considered

**Pure vector search (replace BM25):**
- Pro: Simpler query path; no score fusion needed; handles all query types uniformly
- Con: Vector search alone has worse precision on head queries where exact keyword matches are more reliable; loss of traditional IR guarantees (e.g., exact phrase matching)
- Rejected because: Head query quality would regress, which affects the majority of query volume; hybrid approach preserves existing quality while adding semantic recall

**Self-hosted sentence-transformers model:**
- Pro: No per-token cost; no external API dependency; full control over model versioning
- Con: Requires GPU instances for acceptable embedding throughput (4 million embeddings/day); team has no GPU infrastructure experience; 2-3 month runway to production vs. 3-4 weeks with hosted API
- Rejected because: Time-to-production cost is too high; GPU operational complexity is out of scope for the team's current capabilities; can be revisited once hybrid search is proven in production
