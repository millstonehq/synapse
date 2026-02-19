---
id: WIKI-020
type: wiki
title: Search Indexing Pipeline - Data Flow
status: review
owner: Search Team
created: '2024-01-23T11:52:48.612Z'
updated: '2026-03-21T08:00:44.725Z'
tags:
  - wiki
  - search-platform
summary: Search Indexing Pipeline - Data Flow
source_repo: https://git.example.com/acme/search-indexing-pipeline
commit_sha: b588f697d6969cd1b6a36f9e4e667810914aa744
generated_at: '2025-09-03T09:46:57.123Z'
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
importance: medium
example: true
---

## Overview

The Search Indexing Pipeline ingests content mutation events and transforms them into fully enriched, indexed documents in Elasticsearch. This page traces the data flow from upstream event production through each pipeline stage to the final indexed state, including the side paths for suggestion index updates and embedding generation.

Understanding the data flow is essential for diagnosing indexing latency, debugging missing documents, and planning bulk reindex operations.

## Architecture

The pipeline data flow has three main paths:

**Incremental path (normal operations):**
1. Content service publishes a `ContentMutatedEvent` to Kafka topic `content.mutations` on create, update, or delete.
2. The Ingest Worker reads the event, validates schema, and writes a `pending` record to PostgreSQL `indexing_state`.
3. The Transform Worker enriches the document: extracts structured fields, detects language, selects the Elasticsearch analyzer chain for the document's language and content type.
4. The Embedding Worker fetches or generates a dense vector for the document. Checks Redis cache first; calls OpenAI embedding API on cache miss and writes the result to cache with a 7-day TTL.
5. The Index Writer bulk-indexes the enriched document to Elasticsearch via the `search-content-write` alias and marks the `indexing_state` record as `indexed`.

**Suggestion side path:**
After step 5, the Index Writer also extracts the document title, tags, and any configured suggestion fields and upserts them into the `search-suggestions` DynamoDB table consumed by the Autocomplete Service.

**Bulk reindex path:**
A separate batch job (`reindex-job`) reads all documents from the source-of-truth database (not Kafka), writes them to a new Elasticsearch index, verifies document counts, then atomically updates the `search-content-read` alias to point to the new index. The `reindex-job` runs on a Kubernetes CronJob schedule (weekly) and can be triggered manually.

## Key Components

**PostgreSQL `indexing_state` table:**
Tracks per-document state: `document_id`, `source_version`, `state` (pending/indexed/failed), `attempts`, `last_error`, `indexed_at`. Used for idempotency (prevents double-indexing on Kafka redelivery) and for the retry worker that reprocesses failed documents.

**Redis embedding cache:**
Key format: `embedding:v1:<document_hash>`. TTL 7 days. Hash is SHA-256 of the document's indexable text. Avoids redundant embedding API calls on minor document updates that don't change text content.

**Elasticsearch write alias:**
`search-content-write` always points to the current write index. During bulk reindex, the write alias switches to the new index after the old index is fully copied, preventing writes to a stale index.

## Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Kafka consumer group | `search-indexing-workers` | One group per worker type |
| Bulk index batch size | 500 documents | Tunable; reduce on Elasticsearch backpressure |
| Embedding batch size | 32 documents | Matches OpenAI embedding API batch limit |
| Max indexing retries | 3 | Exponential backoff; failures go to DLQ after 3rd attempt |
| Reindex verification threshold | 99.5% document count match | Below threshold → reindex aborted, alias not swapped |
