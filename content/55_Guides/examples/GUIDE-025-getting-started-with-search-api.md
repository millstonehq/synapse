---
id: GUIDE-025
type: guide
title: Getting Started with Search API
status: draft
owner: Developer Experience
created: '2024-10-14T21:50:27.943Z'
updated: '2026-10-02T13:40:55.023Z'
tags:
  - guide
  - search-platform
summary: Getting Started with Search API
audience: partner
related_systems:
  - SYSTEM-024
  - SYSTEM-025
related_sops:
  - SOP-045
  - SOP-043
example: true
---

## Why This Matters

The Search API is the primary interface for surfacing indexed content to users. Whether you are building a product search page, an internal knowledge tool, or a multi-faceted catalog browser, understanding how to construct well-formed queries and interpret responses will save you significant debugging time and help you build faster, more relevant search experiences from day one.

## Prerequisites

Before making your first API call, ensure you have the following:

- An API key issued by the Search Platform team (request via the developer portal)
- The base URL for the environment you are targeting (staging or production)
- Familiarity with the response envelope shape documented in the Search API Response Format Standard
- A registered content type to search against; coordinate with the Search Platform team if you are querying a new content domain

## Making Your First Query

The basic search request uses a single `q` parameter for the query string:

```
GET /v1/search?q=network+security&size=10
```

The response envelope will include a `meta` object with `query_id`, `total_hits`, and `took_ms`, and a `results` array of matching documents. Each result includes `id`, `score`, `source` (the full document fields), and `highlights` for rendering matched terms.

To filter results by a specific field, use the `filter[field_name]` parameter pattern:

```
GET /v1/search?q=network+security&filter[content_type]=article&filter[status]=published
```

## Pagination and Sorting

For result sets beyond the first page, use the `next_cursor` token returned in the response:

```
GET /v1/search?q=network+security&cursor=<token-from-previous-response>
```

Cursor tokens are opaque — do not parse or construct them manually. To sort results, append the `sort` parameter:

```
GET /v1/search?q=network+security&sort=published_date:desc
```

## Common Integration Mistakes

- **Sending raw PII in query strings**: Query strings are logged (hashed). Do not send names, email addresses, or account numbers as search terms. Pre-process user input to strip sensitive tokens before sending to the API.
- **Using large `size` values without pagination**: Requesting `size=500` in a single call creates high memory pressure on the cluster. Use cursor-based pagination with `size=20` and fetch subsequent pages on demand.
- **Ignoring the `query_id` in the response**: The `query_id` is essential for associating click-through and relevance feedback events with the originating query. Always store it and send it with interaction events.

## Next Steps

- Review the full query parameter reference in the Search API documentation portal
- Explore faceted search using the `facets` parameter to build filter UIs
- Implement click-through event tracking using the analytics event schema to contribute to relevance improvement
