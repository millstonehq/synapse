---
id: TDD-024
type: tdd
title: Search Analytics Pipeline TDD
status: approved
owner: Principal Engineer
created: '2025-03-31T03:10:28.744Z'
updated: '2025-01-27T21:35:42.846Z'
tags:
  - tdd
  - search-platform
summary: Search Analytics Pipeline TDD
related_adrs:
  - ADR-0019
  - ADR-0018
example: true
---

## Summary

Design the Search Analytics Pipeline that ingests search interaction events (queries, impressions, clicks), computes real-time and batch aggregates (CTR, MRR, zero-result rate), and feeds the resulting signals back to the ranking and autocomplete systems. The pipeline must handle 15 million events per day with end-to-end processing lag under 60 seconds, consistent with the search engine choices in [[ADR-0018|ADR-0018]] and the hybrid search signal requirements in [[ADR-0019|ADR-0019]].

## Overview

The analytics pipeline is a multi-stage event processing system. Events flow from frontend clients through Kinesis, are processed by ECS Fargate consumers, and are written to two sinks: OpenSearch for long-term storage and dashboarding, and Redis for real-time signal computation. The real-time signals are consumed by the Search Relevance Engine and Search Autocomplete Service.

Key design principles:
- **At-least-once delivery**: Events may be delivered more than once; consumers must deduplicate by event ID
- **Schema validation at ingest**: Invalid events are rejected at the API boundary and sent to a dead-letter queue, not silently dropped
- **Signal isolation**: Real-time signals (CTR, frequency) are written to Redis; long-term analytics are written to OpenSearch. The two stores have different availability requirements.

## Architecture

- **Event API**: HTTP endpoint that accepts batched events (max 1,000 per request) from frontend clients. Validates event schema, assigns server timestamps, publishes to Kinesis `search-events` stream.
- **Stream Consumer**: ECS Fargate tasks that consume from Kinesis. Each consumer processes events in batches of 500, deduplicates by `event_id`, and routes to two writers.
- **OpenSearch Writer**: Bulk-indexes events to the `search-events-{YYYY-MM}` index for long-term retention and dashboard queries.
- **Redis Aggregator**: Updates rolling 24h CTR counters in Redis using hash increment operations. Key format: `ctr:{query_hash}:{doc_id}`, TTL 48h.
- **Batch Aggregator**: Scheduled job (every 5 minutes) that reads Redis CTR counters, computes aggregate signals (CTR per query/result pair, MRR per query), and writes to Aurora PostgreSQL `relevance_signals` table for the Relevance Engine.

## Information Model

- **SearchEvent**: `{ event_id: UUID, session_id: string, user_id?: string, event_type: 'query'|'impression'|'click', query: string, result_id?: string, position?: number, timestamp: ISO8601 }`
- **CTRCounter** (Redis): hash `ctr:{query_hash}:{doc_id}` with fields `impressions: int`, `clicks: int`, TTL 48h
- **RelevanceSignal** (Aurora): `{ query_hash: string, document_id: string, ctr_24h: float, impressions_24h: int, computed_at: ISO8601 }`
- **AnalyticsEvent** (OpenSearch): Full event record with server-assigned `indexed_at` timestamp, retained for 90 days hot / 1 year cold

## Interfaces

- `POST /v1/analytics/events` — batch event ingest endpoint; accepts `{ events: SearchEvent[] }`; returns `{ accepted: int, rejected: int, errors: string[] }`
- `KinesisConsumer.process(records: KinesisRecord[]): Promise<void>` — main consumer loop
- `RedisAggregator.increment(queryHash: string, docId: string, eventType: 'impression'|'click'): Promise<void>`
- `BatchAggregator.run(): Promise<AggregationResult>` — scheduled signal computation
- Signal read interface: `RedisAggregator.getSignals(queryHash: string): Promise<CTRSignal[]>` — used by autocomplete

## Files and Layout

```
src/
  api/
    handler.ts          - HTTP event ingest endpoint
    validator.ts        - Event schema validation
    publisher.ts        - Kinesis publish with batching
  consumer/
    kinesis-consumer.ts - Kinesis stream reader and dispatcher
    deduplicator.ts     - Event ID deduplication (Redis bloom filter)
    opensearch-writer.ts
    redis-aggregator.ts
  aggregator/
    batch-aggregator.ts - Scheduled 5-min aggregation job
    aurora-writer.ts    - Relevance signal persistence
  config.ts
tests/
```

## Work Plan

1. **Phase 1 (Week 1-2)**: Event API with schema validation and Kinesis publishing; deduplication logic
2. **Phase 2 (Week 3)**: Kinesis consumer with OpenSearch writer; integration test with local Kinesis emulator
3. **Phase 3 (Week 4)**: Redis CTR aggregation; validate counter accuracy with synthetic event load
4. **Phase 4 (Week 5)**: Batch aggregator and Aurora signal writer; integration with Relevance Engine signal reader
5. **Phase 5 (Week 6)**: Production deployment; validate end-to-end lag < 60 seconds under load

## Risks and Mitigations

- **Risk**: Kinesis consumer lag under traffic spikes delays signal updates. **Mitigation**: Consumer autoscaling on shard lag metric; 7-day Kinesis retention allows replay if consumers fall behind.
- **Risk**: Redis CTR counters become inaccurate due to hash collision in `query_hash`. **Mitigation**: Use 64-bit hash of normalized query; collision probability negligible at current query vocabulary size.
- **Risk**: OpenSearch write throughput becomes a bottleneck at 15M events/day. **Mitigation**: Bulk indexing with 500-event batches; OpenSearch ISM policy rolls over indices daily; monitor write latency.
