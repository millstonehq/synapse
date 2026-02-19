---
id: ADR-0020
type: adr
title: Use Separate Read and Write Indices
status: approved
owner: Tech Lead
created: '2025-08-07T20:00:39.762Z'
updated: '2025-08-29T17:50:39.967Z'
tags:
  - adr
  - search-platform
summary: Use Separate Read and Write Indices
example: true
---

## Context

The Search Indexing Pipeline writes approximately 200,000 document mutations per day to Elasticsearch, while the Search Query Processing Service executes 12 million queries per day against the same index. Both operations compete for Elasticsearch cluster resources — specifically, bulk indexing requires merge thread activity and write I/O that can elevate query latency.

Additionally, we need to support periodic full reindexes (for schema migrations, analyzer changes, or relevance tuning) that must complete without disrupting query traffic. A full reindex currently takes 4-6 hours and would be disruptive if it shared the same index as live queries.

Two approaches were evaluated: (1) a single index for both reads and writes, with throttling on the bulk indexing path to protect query latency, and (2) separate read and write indices with an alias-based promotion step.

## Decision

We will use **Elasticsearch index aliases** to maintain logically separate read and write paths:

- `search-content-read` alias points to the currently active query index
- `search-content-write` alias points to the currently active write index (same physical index during normal operations; diverges only during reindex)

During normal operations, both aliases point to the same physical index (e.g., `search-content-v7`). During a reindex operation, `search-content-write` is pointed to the new index (`search-content-v8`) while `search-content-read` continues to serve queries from `search-content-v7`. When the reindex completes and document counts are verified, `search-content-read` is atomically swapped to `search-content-v8`.

## Consequences

**Positive:**
- Reindexing is completely transparent to query traffic; zero-downtime index migrations
- Read and write operations can be throttled independently via Elasticsearch index settings on their respective physical indices
- The alias swap is atomic in Elasticsearch — no window where queries hit an intermediate state
- Easy rollback: if a reindex produces bad results, repointing `search-content-read` back to the previous index takes milliseconds

**Negative:**
- During a reindex, writes go to the new index only; the old index is read-only. Any queries that need documents written during the reindex window will not find them until the alias swap completes. This creates a brief window of eventual consistency.
- The alias swap must be automated with verification checks to prevent swapping to an under-populated index; a manual mistake could take the search service down.
- Adds operational complexity — engineers must understand the alias model to avoid writing directly to the physical index name.

**Neutral:**
- Storage cost doubles temporarily during a reindex (two full copies of the index exist simultaneously)
- The alias pattern is a well-documented Elasticsearch best practice; documentation and runbooks can reference community resources

## Alternatives Considered

**Single index with indexing throttle:**
- Pro: Simpler — one index, no alias management; less storage during normal operations
- Con: Reindexing while serving queries causes write amplification and GC pressure; live reindex requires careful throttling and still risks latency spikes; no clean rollback path if reindex produces a worse index
- Rejected because: The reindex use case is frequent enough (weekly planned reindex, ad-hoc migrations) that the operational risk of competing with live traffic is too high

**Shadow replicas (Elasticsearch Shadow Replica feature):**
- Pro: Allows a secondary replica to catch writes during a reindex without alias management
- Con: Elasticsearch Shadow Replicas were deprecated and removed in Elasticsearch 6.x; not available on 8.x
- Rejected because: Feature is not available in our target version
