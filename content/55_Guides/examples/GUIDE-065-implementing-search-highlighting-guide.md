---
id: GUIDE-065
type: guide
title: Implementing Search Highlighting Guide
status: draft
owner: Developer Experience
created: '2025-04-04T03:34:57.766Z'
updated: '2026-09-23T14:58:53.812Z'
tags:
  - guide
  - search-platform
audience: partner
related_systems:
  - SYSTEM-023
  - SYSTEM-024
related_sops:
  - SOP-048
  - SOP-041
example: true
---

## Why This Matters

Search result highlighting — showing users which parts of a document matched their query — is one of the most effective ways to improve search result comprehension and click-through rate. Without highlighting, users must scan each result summary to determine relevance. With highlighting, the matching terms are visually marked in the excerpt, enabling users to make relevance judgments in milliseconds.

This guide explains how our search highlighting pipeline works, how to request highlights from the Search Query Processing Service, and how to render them correctly in the frontend. It covers both body excerpt highlighting and title term highlighting, which behave differently in our implementation.

## How Highlighting Works in Elasticsearch

Elasticsearch's highlighting API post-processes matched documents and returns HTML-tagged snippets of the matched fields. Our pipeline uses the `unified` highlighter (default in ES 8.x), which uses the BM25 scoring model to select the most relevant passages from the document body.

The key configuration options we use:

- `number_of_fragments`: How many excerpt passages to return (we use `3`)
- `fragment_size`: Target character length per passage (we use `150` characters)
- `pre_tags` / `post_tags`: HTML tags wrapping matched terms (we use `<mark>` / `</mark>`)
- `require_field_match: false`: Allows highlighting on the `body` field even when the query matched a different field (e.g., `title`)
- `index_options: offsets` on the `body` field mapping: Required for the unified highlighter to work efficiently on large documents. This is already configured in the production index template.

For the `title` field, we use the `plain` highlighter (set explicitly) because title text is short and the unified highlighter's passage scoring provides no benefit for single-line fields.

## Requesting Highlights from the Search API

The Search Query Processing Service (`[[SYSTEM-023|Search Autocomplete Service]]` handles autocomplete; the main search endpoint is served by the Lambda in SYSTEM-023's sibling service) accepts a `highlight` query parameter.

Pass `highlight=true` in the GET request:

```
GET /v1/search?q=elasticsearch+indexing&page=1&limit=20&highlight=true
```

When `highlight=true`, the response includes a `highlights` object on each result:

```json
{
  "results": [
    {
      "document_id": "doc-12345",
      "title": "Elasticsearch Indexing Pipeline Design",
      "excerpt": "...",
      "url": "/docs/elasticsearch-indexing-pipeline",
      "content_type": "documentation",
      "publish_date": "2025-03-15",
      "highlights": {
        "title": ["<mark>Elasticsearch</mark> <mark>Indexing</mark> Pipeline Design"],
        "body": [
          "The <mark>indexing</mark> pipeline processes content mutations...",
          "The <mark>Elasticsearch</mark> cluster uses a write alias to..."
        ]
      }
    }
  ]
}
```

The `highlights.title` array always contains one element (the full title with marked terms). The `highlights.body` array contains up to 3 passage fragments. If a field had no matches (e.g., the query matched on `tags` but not `body`), that field is omitted from the `highlights` object.

## Rendering Highlights Safely

The highlight strings contain raw HTML (`<mark>` tags). You **must** render them as HTML, not as plain text. However, the rest of the text content within the highlight has been HTML-escaped by Elasticsearch — angle brackets and ampersands in the original document are already escaped before the `<mark>` tags are inserted. This means you can safely use `innerHTML` to render the highlight strings without additional sanitization for XSS risk from the document content itself.

Example (React):

```jsx
function SearchResultHighlight({ highlights }) {
  if (!highlights?.body?.length) return null;
  return (
    <div className="search-highlights">
      {highlights.body.map((fragment, i) => (
        <p
          key={i}
          className="search-highlight-fragment"
          dangerouslySetInnerHTML={{ __html: `…${fragment}…` }}
        />
      ))}
    </div>
  );
}
```

For the title, use the highlighted version when available so matched terms are visually marked in the result heading:

```jsx
function SearchResultTitle({ title, highlights, url }) {
  const displayTitle = highlights?.title?.[0] ?? title;
  return (
    <a
      href={url}
      className="search-result-title"
      dangerouslySetInnerHTML={{ __html: displayTitle }}
    />
  );
}
```

## CSS Styling for Highlights

The `<mark>` element renders with a default browser yellow background. Override this in your stylesheet to match your design system:

```css
.search-highlight-fragment mark,
.search-result-title mark {
  background-color: #fff3cd;  /* soft amber, accessible contrast */
  color: inherit;
  padding: 0 2px;
  border-radius: 2px;
  font-style: normal;
}
```

Avoid bold or italic for highlight marks — studies show that background color alone is sufficient for users to identify matches, and additional text decoration increases visual noise.

## Performance Considerations

Highlighting adds approximately 5-15ms to query latency in our cluster (measured at P95). This is well within the 200ms P95 latency SLO. However, there are two scenarios where highlighting can degrade performance:

1. **Very large documents**: Documents with a body field over 100KB trigger a slower highlighting path. The analytics collector (see `[[SYSTEM-024|Search Analytics Collector]]`) tracks `highlight_latency_ms` as a metric. If documents with highlight latency > 50ms are common in your content type, consider setting `number_of_fragments: 1` to reduce the highlighting work.

2. **High-volume bulk API calls**: If you are building a feature that needs to fetch large numbers of search results (e.g., a content export or admin view), do not request highlights — the highlighting CPU cost scales with result set size. Only request `highlight=true` for user-facing search result pages.

## Common Pitfalls

**Pitfall: Highlighting shows no matches even though the document ranked highly.** This can happen when a document ranked due to a match on the `tags.text` field but has no `tags` field in the highlight configuration. The `require_field_match: false` setting handles the `body` field but does not automatically apply to all fields. If you add new field boosts, update the highlight configuration in the Lambda function alongside the query.

**Pitfall: Highlight fragments cut words in half.** Elasticsearch's `fragment_size` is a target, not a hard limit, and the unified highlighter respects sentence boundaries. However, passages can still be truncated mid-word if a sentence is very long. Add `"boundary_scanner": "sentence"` with `"boundary_max_scan": 100` in the highlight configuration to prefer sentence-boundary splits.

**Pitfall: Using `highlight=true` in the autocomplete API.** The autocomplete endpoint (`/v1/suggest`) does not support highlighting. Highlights are only available from the main search endpoint (`/v1/search`).

## Next Steps

- Review the `[[SOP-048|Search API Integration SOP]]` for the full request/response contract including authentication and rate limits
- Review the `[[SOP-041|Search Index Mapping SOP]]` if you need to add a new field that should be highlighted
- Check the [Search API Staging Environment](https://search-platform-staging.example.com/v1/search?q=test&highlight=true) to verify highlighting behavior before deploying to production
