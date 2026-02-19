---
id: FLOW-018
type: flow
title: Content Indexing Pipeline Flow
status: draft
owner: QA Lead
created: '2025-05-28T00:18:55.025Z'
updated: '2026-12-24T03:55:27.393Z'
tags:
  - flow
  - search-platform
summary: Content Indexing Pipeline Flow
feature_area: Search Platform
related_prds:
  - PRD-025
example: true
---

## Steps

### Step 1: Content Mutation Event Published

A content author publishes or updates a document in the content management system. The CMS publishes a `ContentMutatedEvent` to the Kafka topic `content.mutations`. The event includes: document ID, content type, the full document payload (title, body, metadata), and the mutation type (create, update, delete). For delete events, only the document ID is included.

### Step 2: Ingest and Deduplication

The Ingest Worker consumes the Kafka event, validates the schema, and checks the PostgreSQL `indexing_state` table for a record with the same document ID and content version hash. If a matching record exists and is in `indexed` state, the event is a duplicate and is acknowledged without reprocessing. Otherwise, a new `pending` record is written to `indexing_state` and the document is passed to the Transform Worker queue.

### Step 3: Document Transformation

The Transform Worker enriches the document: it strips HTML from the body, extracts structured fields (word count, estimated reading time, internal link targets), detects the document language using a language detection library, and selects the appropriate Elasticsearch analyzer chain based on content type and language. The output is a normalized document payload ready for indexing.

### Step 4: Embedding Generation

The Embedding Worker receives the normalized document and computes a dense vector embedding. It first checks the Redis embedding cache using the SHA-256 hash of the document's indexable text as the key. On a cache hit, the cached vector is used. On a cache miss, the worker calls the OpenAI text-embedding-3-small API in a batch of up to 32 documents. The result is written to Redis with a 7-day TTL.

### Step 5: Index Write and State Update

The Index Writer bulk-indexes the enriched document (with `content_vector` field) to Elasticsearch via the `search-content-write` alias. It also upserts the document's title and tags into the DynamoDB `search-suggestions` table for autocomplete. After a successful Elasticsearch write, the `indexing_state` record for the document is marked `indexed`. For delete events, the document is deleted from both the Elasticsearch index and the DynamoDB suggestions table.

## Expected Results

- A newly published document is searchable by keyword within 10 seconds of the Kafka event being published
- A newly published document is searchable by semantic similarity within 5 minutes (embedding generation is asynchronous but fast)
- The document's title appears in autocomplete suggestions within 5 minutes of indexing
- Delete events remove the document from all search surfaces within 30 seconds
- If the embedding API is unavailable, the document is indexed without a vector and backfilled when the API recovers

## User Info

| Field | Value |
|-------|-------|
| Role | Content author (publisher) / Search Platform QA |
| Permissions | Write access to content CMS; no direct Elasticsearch access |
| Test document ID | test-doc-20250101-001 (staging environment) |
| Environment | Staging (Kafka topic: content.mutations.staging) |
| Monitoring | Grafana indexing pipeline dashboard (staging) |
