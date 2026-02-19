---
id: WIKI-017
type: wiki
title: Search Platform - Architecture Overview
status: draft
owner: Search Team
created: '2025-05-25T01:04:49.436Z'
updated: '2026-08-19T20:50:05.115Z'
tags:
  - wiki
  - search-platform
summary: Search Platform - Architecture Overview
source_repo: https://git.example.com/acme/search-platform
commit_sha: 8136ad1d5f56a7b046252a1dd2ad9b0bb8f521c2
generated_at: '2025-03-19T03:17:29.563Z'
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
importance: medium
example: true
---

## Overview

The Search Platform is a collection of five cooperating services that together provide full-text, faceted, and hybrid (keyword + vector) search for the product catalog and content surfaces. It is built on Elasticsearch 8.x as the primary index store and is designed around a read-heavy workload (12M queries/day) with an asynchronous write path (200K document mutations/day).

The platform separates concerns into distinct services: query processing, indexing, autocomplete, analytics collection, and relevance re-ranking. This separation allows each service to scale and be deployed independently.

## Architecture

The platform's request path flows through four layers:

- **Client Layer**: Web and mobile clients issue search queries to the Query Processing Service via REST. Autocomplete requests are sent to the Autocomplete Service concurrently with keystroke events.
- **Query Processing**: The Search Query Processing Service parses, rewrites, and executes queries against Elasticsearch. It optionally invokes the Search Relevance Engine for ML-based re-ranking.
- **Index Layer**: Elasticsearch 8.x hosts the primary search index (keyword + dense_vector fields), the suggestions index, and the analytics index. Read and write traffic are separated via index aliases.
- **Write Path**: The Search Indexing Pipeline consumes content mutation events from Kafka, enriches documents, generates embeddings, and bulk-writes to Elasticsearch via the write alias.

Analytics events flow separately: the Search Analytics Collector ingests click and impression events, aggregates CTR signals, and feeds them back to the Autocomplete Service and Relevance Engine.

## Key Components

- **Search Query Processing Service**: Stateless Lambda functions; handles query parsing, rewrite, fan-out, and ranking merge. Entry point for all search queries.
- **Search Indexing Pipeline**: Kubernetes-deployed workers; responsible for the full document enrichment and write path.
- **Search Autocomplete Service**: Lambda-backed, DynamoDB-fronted; returns prefix-matched suggestions ranked by popularity.
- **Search Analytics Collector**: ECS Fargate; ingests interaction events via Kinesis and computes CTR aggregates.
- **Search Relevance Engine**: ECS Fargate, Java 21; LightGBM-based re-ranking with a 30ms timeout budget.

## Configuration

Key configuration surface areas:

- Elasticsearch index settings (shards, replicas, analyzer chains) are managed via index templates in the `search-indexing-pipeline` repo
- Query rewrite rules (synonyms, stopwords, field boosts) are stored in DynamoDB `search-query-config` and loaded at Lambda cold start
- Relevance model artifacts are stored in S3 `search-models-prod` and hot-swapped without service restart
- Feature flags for hybrid search, re-ranking, and personalization are managed via LaunchDarkly

## Dependencies

| Service | Depends On | Purpose |
|---------|-----------|---------|
| Query Processing | Elasticsearch, Relevance Engine | Index queries, re-rank results |
| Indexing Pipeline | Kafka, Elasticsearch, Embedding API | Ingest and enrich documents |
| Autocomplete | DynamoDB, Analytics Collector signals | Serve prefix suggestions |
| Analytics Collector | Kinesis, OpenSearch, Redis | Capture and aggregate click events |
| Relevance Engine | Aurora PostgreSQL, ElastiCache | Score and re-rank candidates |
