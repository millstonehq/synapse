---
id: SYSTEM-022
type: system
title: Search Indexing Pipeline
status: approved
owner: Search Engineering
owner_team: Search Engineering
runtime: Kubernetes / Node.js 20 / PostgreSQL 16
created: '2024-02-18T13:53:06.375Z'
updated: '2025-01-17T09:10:01.977Z'
tags:
  - system
  - search-platform
summary: Search Indexing Pipeline
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/search-indexing-pipeline
dependencies:
  - Search Autocomplete Service
  - Search Relevance Engine
runbooks:
  - RUNBOOK-031
  - RUNBOOK-032
example: true
---

## Overview

The Search Indexing Pipeline is responsible for ingesting content from upstream producers, transforming it into search-optimized documents, and writing them into the Elasticsearch indices consumed by the query layer. It supports both real-time incremental indexing (via Kafka) and bulk reindexing jobs.

The pipeline processes approximately 200,000 document mutations per day. Documents flow through enrichment stages including field extraction, language detection, text analysis configuration selection, and vector embedding generation before being written to the target index. The pipeline also maintains the suggestion index consumed by the Search Autocomplete Service.

## Architecture

The pipeline is structured as a series of Kubernetes-deployed worker stages:

- **Ingest Worker**: Consumes events from Kafka topic `content.mutations`. Validates schema, deduplicates by document ID, and forwards to the transformation queue.
- **Transform Worker**: Applies field extraction rules per content type, strips HTML, detects language, and selects the appropriate Elasticsearch analyzer. Outputs a normalized document.
- **Embedding Worker**: Calls the embedding service to generate dense vectors for hybrid search. Batches requests to the embedding provider in groups of 32. Results are cached in Redis by document hash.
- **Index Writer**: Bulk-indexes transformed documents into Elasticsearch using the write alias. Handles backpressure by monitoring queue depth and pausing ingestion when the cluster is under write pressure.
- **State Tracker**: Persists per-document indexing state in PostgreSQL 16 for idempotency and reprocessing.

## Repositories

- [search-indexing-pipeline](https://git.example.com/acme/search-indexing-pipeline) - Pipeline workers, Kubernetes manifests, migration scripts

## Runtime Environment

- **Platform**: Kubernetes, 3 replicas per worker type, horizontal pod autoscaling on queue depth
- **Language**: Node.js 20 with TypeScript
- **Message broker**: Kafka (MSK) — topic `content.mutations`, 12 partitions
- **State store**: PostgreSQL 16 (Aurora Serverless v2) for indexing state and retry tracking
- **Cache**: Redis 7 for embedding vector caching
- **Deployment**: ArgoCD; rolling updates with queue drain before pod termination

## Dependencies

- Kafka (MSK) — event source for incremental indexing
- Elasticsearch 8.x — write target via write alias
- Embedding provider (OpenAI text-embedding-3-small) — vector generation
- PostgreSQL 16 (Aurora) — indexing state and deduplication
- Redis 7 — embedding cache
- Search Autocomplete Service — suggestion index refresh triggers
- Search Relevance Engine — relevance signal refresh after bulk reindex

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Indexing lag | P95 < 30 seconds from mutation event to searchable |
| Error rate | < 0.1% failed documents (excluding invalid source data) |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-031|Search Indexing Pipeline Backlog Runbook]]
- [[RUNBOOK-032|Search Index Writer Errors Runbook]]
