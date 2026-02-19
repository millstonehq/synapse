---
id: FLOW-019
type: flow
title: Search Suggestion Generation Flow
status: approved
owner: QA Lead
created: '2025-04-20T17:26:14.325Z'
updated: '2026-11-08T13:09:21.299Z'
tags:
  - flow
  - search-platform
summary: Search Suggestion Generation Flow
feature_area: Search Platform
related_prds:
  - PRD-024
example: true
---

## Steps

### Step 1: Keystroke Event and Debounce

The user begins typing in the search box. The frontend captures each keystroke and applies a 150ms debounce to avoid issuing a request on every character. Once the debounce threshold passes with no additional input and the query prefix has at least 2 characters, the frontend issues a GET request to the Autocomplete Service: `GET /v1/suggest?q={encoded_prefix}&limit=8`. The request includes the user's session cookie and, if logged in, a JWT bearer token.

### Step 2: Prefix Shard Routing

The Autocomplete Service Lambda receives the request and computes a shard key from the first two characters of the prefix using a deterministic hash function. The prefix is mapped to one of 16 DynamoDB shards using the scatter-gather strategy. The Lambda issues up to 16 parallel DynamoDB `Query` calls against the `search-suggestions` table using a partition key of `shard#{n}#{prefix}` and a sort key prefix scan. Partial results from available shards are merged; shards that timeout (>20ms) are skipped without error.

### Step 3: CTR-Based Ranking

The merged candidate list of suggestion records is ranked using a composite score: `score = 0.6 * normalized_frequency + 0.4 * ctr_score`. The `ctr_score` for each suggestion is fetched from the Redis signal cache (key: `suggest:ctr:{term_hash}`) which is refreshed from the analytics pipeline every 5 minutes. On a Redis cache miss, the stored base CTR from DynamoDB is used directly. The top 8 results by score are selected.

### Step 4: Personalization Boost (Logged-In Users)

If the request includes a valid JWT, the Lambda fetches the user's 30-day query history from the `UserHistoryRecord` DynamoDB table (partition key: `user#{hashed_user_id}`). Any suggestion terms that match entries in the user's recent query history receive a +0.15 score boost. The result list is re-sorted with boosts applied. This step is skipped entirely for anonymous users; no user history lookup is attempted.

### Step 5: Response and Impression Tracking

The Lambda serializes the final ordered list of up to 8 suggestions with their category labels and returns the JSON response. The frontend renders the suggestion dropdown below the search box. An impression event (`SuggestionImpression`) is fired asynchronously to the analytics event pipeline with the suggestion list, prefix, and session ID. The total round-trip from keystroke debounce to dropdown render must complete within 50ms P99.

## Expected Results

- The suggestion dropdown appears within 50ms P99 of the debounce threshold being reached
- Up to 8 suggestions are shown, ranked by historical popularity and CTR
- Logged-in users with matching query history see personalized suggestions boosted above generic completions
- If DynamoDB is unavailable or all shard queries time out, an empty list is returned silently (no 503 error visible to the user)
- Suggestion impression events are recorded in the analytics pipeline for subsequent CTR computation
- The suggestion index reflects document titles and tags upserted by the most recent indexing pipeline run

## User Info

| Field | Value |
|-------|-------|
| Role | Authenticated user or anonymous visitor |
| Permissions | Read-only access to suggestion index |
| Test account | search-test@example.com (staging environment) |
| Environment | Staging (search-platform-staging.example.com) |
| Monitoring | [[PRD-024|Search Analytics Dashboard]] — autocomplete CTR metric |
