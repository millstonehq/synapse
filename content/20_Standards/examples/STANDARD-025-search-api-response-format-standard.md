---
id: STANDARD-025
type: standard
title: Search API Response Format Standard
status: approved
owner: Security Lead
created: '2025-08-09T12:27:15.097Z'
updated: '2025-08-08T12:01:16.665Z'
tags:
  - standard
  - search-platform
summary: Search API Response Format Standard
related_policies:
  - POLICY-024
  - POLICY-025
example: true
related_systems:
  - SYSTEM-024
  - SYSTEM-023
---

## Area

This standard defines the required JSON structure for all responses returned by the Search Platform's public and internal query APIs. It covers the top-level response envelope, result document shape, pagination tokens, facet payloads, and error response format. All search API endpoints must conform to this standard regardless of the underlying query engine.

## Controls

- All search responses must include a top-level `meta` object containing `query_id`, `total_hits`, `took_ms`, and `ranking_model_version`
- Result documents must be returned in a `results` array; each item must include `id`, `score`, `source`, and `highlights` fields
- Pagination must use opaque cursor tokens in a `next_cursor` field; offset-based pagination is not permitted for responses exceeding 1,000 total hits
- Facet counts must be returned in a `facets` map keyed by field name, with each value containing `buckets` array of `{key, count}` objects
- HTTP error responses must use the standard envelope `{error: {code, message, request_id}}` and must not expose internal stack traces
- Response `Content-Type` must be `application/json; charset=utf-8` for all non-streaming endpoints

## Compliance Mappings

- OWASP API Security Top 10: API3 (Excessive Data Exposure) - controlled via field projection enforcement
- Internal API Governance Framework v2: Section 4.2 (Response Envelope Consistency)

## Related Policies

- [[POLICY-024|Search Content Moderation Policy]]
- [[POLICY-025|Search Infrastructure Scaling Policy]]
