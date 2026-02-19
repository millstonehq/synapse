---
id: FLOW-020
type: flow
title: Search Result Click Tracking Flow
status: draft
owner: QA Lead
created: '2024-03-10T22:39:10.216Z'
updated: '2025-05-15T15:57:25.879Z'
tags:
  - flow
  - search-platform
summary: Search Result Click Tracking Flow
feature_area: Search Platform
related_prds:
  - PRD-023
example: true
---

## Steps

### Step 1: User Clicks a Search Result

The user views the search results page and clicks on a result link. Before the browser navigates to the destination URL, the frontend intercepts the click event via a JavaScript event listener. The click handler extracts the following from the result element's data attributes: `search-query-id` (from the response header of the originating search), `result_position` (1-based index), `document_id`, `content_type`, and `destination_url`.

### Step 2: Click Event Dispatch

The frontend constructs a `SearchClickEvent` payload and dispatches it to the Analytics Collector via a `navigator.sendBeacon` POST to `POST /v1/events/search-click`. Using `sendBeacon` ensures the event is delivered even if the user navigates away before the request completes. The payload includes: `search_query_id`, `session_id`, `user_id` (hashed, or null for anonymous), `document_id`, `position`, `content_type`, `timestamp`, and `query_hash`. The request does not block navigation — the browser proceeds to the destination URL immediately.

### Step 3: Analytics Collector Ingestion

The Analytics Collector service (ECS Fargate/Python) receives the event, validates the schema, and writes the event to the Kinesis Data Stream `search-events`. Events are batched into 100-record chunks and flushed every 5 seconds. The Collector returns HTTP 204 immediately upon validation without waiting for Kinesis confirmation. If Kinesis is unavailable, events are buffered in-process for up to 30 seconds before being dropped (with a counter increment on the `events_dropped` CloudWatch metric).

### Step 4: Stream Processing and Storage

The Kinesis Consumer (ECS Fargate) reads from the `search-events` stream and routes `SearchClickEvent` records to the OpenSearch `search-events-clicks-*` index and the Aurora PostgreSQL `relevance_signals` table. The OpenSearch write feeds the real-time analytics dashboard. The Aurora write is used by the LightGBM relevance model training pipeline, which reads `relevance_signals` to compute click-through rates and mean reciprocal rank per query-document pair. Both writes are idempotent on `(search_query_id, document_id)`.

### Step 5: CTR Signal Propagation

The analytics aggregation job (runs every 5 minutes) recomputes per-term CTR values from the `relevance_signals` table and writes updated `ctr_score` values to the Redis signal cache (`suggest:ctr:{term_hash}`). These updated CTR scores are immediately available to the Autocomplete Service for suggestion re-ranking. The weekly LightGBM training job reads the accumulated `relevance_signals` data to retrain the re-ranking model used by the Search Relevance Engine.

## Expected Results

- Every click on a search result generates a `SearchClickEvent` that is delivered to the analytics pipeline within 5 seconds
- Click events are correlated to the originating search session via `search_query_id`
- Position-1 click rate and overall CTR are updated in the analytics dashboard within 15 minutes of clicks occurring
- CTR signal cache in Redis is refreshed every 5 minutes, keeping autocomplete suggestion ranking current
- No duplicate click events are stored for the same `(search_query_id, document_id)` pair
- If the Analytics Collector is unavailable, the user's navigation to the destination URL is unaffected

## User Info

| Field | Value |
|-------|-------|
| Role | Authenticated user or anonymous visitor |
| Permissions | Read access to search results; no direct analytics access |
| Test account | search-test@example.com (staging environment) |
| Environment | Staging (search-platform-staging.example.com) |
| Monitoring | [[PRD-023|Search Suggestions and Autocomplete PRD]] — autocomplete CTR and P99 latency |
