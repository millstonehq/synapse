---
id: GUIDE-028
type: guide
title: Implementing Faceted Search
status: approved
owner: Developer Experience
created: '2024-01-08T17:54:24.264Z'
updated: '2026-01-25T08:15:59.577Z'
tags:
  - guide
  - search-platform
summary: Implementing Faceted Search
audience: partner
related_systems:
  - SYSTEM-025
  - SYSTEM-023
related_sops:
  - SOP-045
  - SOP-048
example: true
---

## What Is Faceted Search

Faceted search allows users to progressively narrow a result set by selecting values from category dimensions (facets) such as content type, date range, author, or status. Rather than returning one flat list of results, the API returns both the matching documents and a set of counts showing how many results fall into each facet bucket — enabling users to filter interactively without issuing a new full-text query for every click.

## Requesting Facets from the API

Include the `facets` parameter in your search request to request facet counts alongside results:

```
GET /v1/search?q=security+policies&facets=content_type,status,author
```

The response `facets` object will contain bucket arrays for each requested facet field:

```json
{
  "facets": {
    "content_type": {
      "buckets": [
        {"key": "policy", "count": 14},
        {"key": "guide", "count": 8},
        {"key": "runbook", "count": 3}
      ]
    }
  }
}
```

## Applying Facet Filters

When a user selects a facet value, add it as a filter in the next request. The API maintains the full result set for facet count calculation while returning only the filtered subset as results:

```
GET /v1/search?q=security+policies&filter[content_type]=policy&facets=status,author
```

Note that the `content_type` facet is removed from the facets request after it is applied as a filter — there is no need to show bucket counts for a dimension the user has already selected.

## Index Mapping Requirements for Faceting

Faceted search requires fields to be mapped as `keyword` type (not `text`) in the Elasticsearch index. Text fields are tokenized and cannot be used for aggregations. If a field needs both full-text search and faceting, use a `fields` mapping to index it as both:

```json
{
  "mappings": {
    "properties": {
      "author": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword", "ignore_above": 256}
        }
      }
    }
  }
}
```

Always use `author.keyword` (not `author`) as the facet field name in requests.

## Performance Considerations

Facet aggregations add overhead to every query. Keep the following in mind:

- Limit the number of facets requested per query to those actively displayed in the UI (typically 3-5)
- Use the `size` parameter on individual facets to cap bucket counts; requesting more than 50 buckets per facet is rarely useful and increases response time
- Consider caching facet counts for popular queries at the application layer to reduce cluster load for high-traffic search pages
