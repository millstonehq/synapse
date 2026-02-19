---
id: WIKI-019
type: wiki
title: Search Ranking Algorithm - Deep Dive
status: approved
owner: Search Team
created: '2025-09-14T02:17:40.904Z'
updated: '2026-01-04T13:41:34.918Z'
tags:
  - wiki
  - search-platform
summary: Search Ranking Algorithm - Deep Dive
source_repo: https://git.example.com/acme/search-ranking-algorithm
commit_sha: 59927d3781c8110d0dd361d9383f9943ba30b0b3
generated_at: '2026-03-06T07:31:14.749Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: high
example: true
---

## Overview

Search ranking on the platform operates in two stages: a retrieval stage that uses Elasticsearch's BM25 scoring with field-specific boosts, and an optional re-ranking stage powered by a LightGBM learn-to-rank model in the Search Relevance Engine. This document explains the mechanics of both stages and the signals that feed into them.

The goal of the ranking pipeline is to maximize NDCG@10 — the probability that a user finds a relevant result in the top 10 positions. The current baseline (BM25 only) achieves NDCG@10 of 0.72. With LightGBM re-ranking, this improves to 0.81 on the held-out evaluation set.

## Architecture

**Stage 1 — BM25 Retrieval:**

Elasticsearch computes a relevance score for each matching document using BM25 with per-field boosts:

- `title^3.0` — Highest weight; exact and partial matches in title are strong signals
- `description^1.5` — Body content; lower weight to avoid keyword stuffing
- `tags^2.0` — Structured metadata; high precision signal
- `content^1.0` — Full document text; catch-all field

Phrase proximity queries use `match_phrase` with a `slop` of 2, boosted by 2x above the base `multi_match` score.

**Stage 2 — LightGBM Re-ranking:**

The Relevance Engine receives the top 100 BM25 candidates and computes 18 features per (query, document) pair:

- BM25 score and rank position from Elasticsearch
- Title exact match flag and prefix match flag
- Click-through rate for (query, document_id) over the past 30 days
- Dwell time (average time on page after click)
- Document recency (exponential decay from publish date)
- Content type (categorical: article, product, guide, etc.)
- Query length (number of tokens)
- User affinity score (if user context provided)

The model outputs a relevance score in [0,1] per candidate. The top 10 by model score are returned as the final result set.

## Key Components

**Synonym expansion** is applied before retrieval using a synonym graph filter in Elasticsearch. Synonyms are maintained in `config/synonyms.txt` in the `search-indexing-pipeline` repo and reloaded via the `_reload_search_analyzers` API.

**Query rewrite rules** (in DynamoDB `search-query-config`) handle special cases: navigational queries are detected by exact-match patterns and bypass re-ranking, landing users directly on the canonical page.

**Hybrid scoring** (when vector search is enabled) combines BM25 and ANN cosine similarity scores via Reciprocal Rank Fusion: `RRF(d) = 1/(k + rank_bm25(d)) + 1/(k + rank_ann(d))` where `k=60`.

## Configuration

Key tunable parameters (managed in DynamoDB `search-query-config`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `title_boost` | 3.0 | BM25 field boost for title |
| `tags_boost` | 2.0 | BM25 field boost for tags |
| `rrf_k` | 60 | RRF constant for hybrid fusion |
| `rerank_candidate_size` | 100 | Candidates passed to LightGBM |
| `rerank_timeout_ms` | 30 | Max wait for Relevance Engine |
