---
id: TDD-023
type: tdd
title: Search Autocomplete Engine TDD
status: proposed
owner: Tech Lead
created: '2024-07-31T02:13:04.906Z'
updated: '2025-05-19T21:20:29.465Z'
tags:
  - tdd
  - search-platform
summary: Search Autocomplete Engine TDD
related_adrs:
  - ADR-0019
  - ADR-0020
example: true
---

## Summary

Design the autocomplete engine that provides real-time prefix-matched query suggestions as users type in the search box. The engine must respond within 50ms P99 and must degrade gracefully without returning errors when the suggestion data store is unavailable. It incorporates click-frequency signals from the Search Analytics Collector for ranking, following the index alias principles in [[ADR-0020|ADR-0020]] and the semantic enrichment direction from [[ADR-0019|ADR-0019]].

## Overview

The autocomplete engine serves prefix completions from a pre-built DynamoDB suggestion table. Suggestions are ranked by a combination of term frequency (from historical queries), click-through rate (from the analytics signal store), and content-type category labels. The engine runs as an AWS Lambda function and must handle 2,000 requests per second at peak.

Key design principles:
- **Silent failure**: DynamoDB timeouts or errors return an empty suggestion list, not a 503 error
- **Prefix sharding**: Suggestion table keys are hashed across 16 logical shards to prevent hot-key throttling
- **Signal freshness**: Click-frequency signals are refreshed every 5 minutes from the analytics store; stale signals are acceptable

## Architecture

- **API Gateway**: Receives GET `/autocomplete?q={prefix}&limit={n}` requests; no authentication required (public endpoint); rate limited at 5,000 req/s per IP
- **Lambda Handler**: Validates input, calls Suggestion Reader, calls Ranker, formats and returns response
- **Suggestion Reader**: Scatter-gather reads across the 16 prefix shards in DynamoDB; collects all candidates for the given prefix; implements 20ms hard timeout per DynamoDB call
- **Ranker**: Combines term frequency, CTR score (from Redis signal cache), and recency signals into a final score; returns top 8 candidates
- **Personalization Layer**: If `user_id` present in request, boosts suggestions matching user's recent query history (DynamoDB per-user TTL table)
- **Signal Cache Refresher**: Background process in Lambda (triggered by separate EventBridge schedule) that reads CTR aggregates from Redis and pre-populates the Lambda's in-memory signal cache

## Information Model

- **SuggestionRecord** (DynamoDB): `{ pk: 'prefix:{prefix}:{shard}', sk: 'suggestion#{term}', term: string, frequency: number, categories: string[], last_updated: ISO8601 }`
- **UserHistoryRecord** (DynamoDB): `{ pk: 'user:{user_id}', sk: 'query#{timestamp}', query: string, TTL: now+30days }`
- **SignalCacheEntry** (Lambda in-memory): `{ term: string, ctr_score: number, fetched_at: number }`
- **AutocompleteResponse**: `{ suggestions: Array<{ text: string, categories: string[], highlighted_prefix: string }>, latency_ms: number }`

## Interfaces

- `GET /autocomplete?q={prefix}&limit={n}&user_id={optional}` — public REST endpoint
- `SuggestionReader.read(prefix: string, limit: number): Promise<SuggestionRecord[]>` — DynamoDB scatter-gather
- `Ranker.rank(suggestions: SuggestionRecord[], signals: SignalCacheEntry[], userId?: string): SuggestionRecord[]` — applies scoring
- `SignalCache.getSignals(terms: string[]): SignalCacheEntry[]` — reads from in-memory cache
- `SignalCacheRefresher.refresh(): Promise<void>` — updates in-memory cache from Redis

## Files and Layout

```
src/
  handler.ts                  - Lambda entry point
  suggestion-reader.ts        - DynamoDB scatter-gather reader
  ranker.ts                   - Scoring and ranking logic
  personalization.ts          - User history boost logic
  signal-cache.ts             - In-memory signal cache with refresh
  formatters.ts               - Response formatting and highlight markup
  config.ts                   - DynamoDB table names, shard count, timeouts
tests/
  handler.test.ts
  ranker.test.ts
  signal-cache.test.ts
  integration/
    autocomplete-e2e.test.ts
```

## Work Plan

1. **Phase 1 (Week 1)**: Implement prefix sharding scheme and DynamoDB table schema; implement Suggestion Reader with scatter-gather and timeout handling
2. **Phase 2 (Week 2)**: Implement Ranker with frequency and CTR scoring; unit tests covering ranking edge cases
3. **Phase 3 (Week 3)**: Implement signal cache refresher and Lambda warm-up behavior; load test at 2,000 req/s on staging
4. **Phase 4 (Week 4)**: Implement personalization layer; A/B test personalized vs. non-personalized suggestions for CTR impact
5. **Phase 5 (Week 5)**: Production deployment with feature flag; monitor P99 latency and error rate

## Risks and Mitigations

- **Risk**: DynamoDB hot-key throttling under viral query trends (as seen in POSTMORTEM-025). **Mitigation**: Prefix sharding across 16 shards distributes load; silent-failure fallback means DynamoDB throttling doesn't cause 503 errors.
- **Risk**: Lambda cold starts exceed 50ms P99 latency budget. **Mitigation**: Provisioned Concurrency set to 100; Lambda size tuned to minimize cold start time.
- **Risk**: Signal cache stale during cache refresh causing inconsistent rankings. **Mitigation**: Cache refresh is in-memory atomic swap; old cache remains active until new cache is fully loaded.
