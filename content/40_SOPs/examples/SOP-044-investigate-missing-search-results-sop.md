---
id: SOP-044
type: sop
title: Investigate Missing Search Results SOP
status: approved
owner: Release Manager
created: '2024-03-21T12:53:18.698Z'
updated: '2026-09-01T18:18:45.640Z'
tags:
  - sop
  - search-platform
summary: Investigate Missing Search Results SOP
related_process: PROCESS-025
related_systems:
  - SYSTEM-023
example: true
---

## Preconditions

- A specific document, entity, or category of results has been reported missing from search results
- You have identified at least one representative query that should return the missing content but does not
- You have access to the Elasticsearch cluster APIs and the ingestion pipeline monitoring dashboards

## Materials/Access

- Elasticsearch query console or cURL access to the cluster
- Ingestion pipeline monitoring dashboard (document processing logs, pipeline lag metrics)
- Grafana: Search Index Health dashboard (document count by index and content type)
- The document ID or content identifier for the reported missing item
- Access to the source system to verify the document's current state

## Procedure

1. Confirm the document exists in the source system and has not been deleted or unpublished. If the document is deleted in the source, its absence from search is expected — close the investigation and communicate this to the reporter.
2. Check the index document count for the affected content type: `GET /<index-name>/_count?q=type:<content-type>`. Compare against the source system count. A significant discrepancy indicates an ingestion gap.
3. Attempt to retrieve the specific document directly by ID: `GET /<index-name>/_doc/<document-id>`. If the document is not found (404), it was either never indexed or was deleted from the index.
4. Search for the document with a highly specific term query to rule out tokenization issues: `POST /<index-name>/_search` with a `term` query on a low-cardinality keyword field (e.g., `id` or `slug`). If the term query finds it but a full-text query does not, the issue is with the analyzer configuration, not indexing.
5. Check the ingestion pipeline logs for the document's ID. Look for errors or failed processing events in the 48-hour window before the issue was first reported.
6. If the document is present in the index but not appearing in search results, run the query with `explain: true` to see why it may be filtered out or scored at zero: `POST /<index-name>/_search` with `"explain": true`.
7. Check for active content filters or blocklist entries that may be suppressing the document. Query the moderation config for the document ID or any matching URL patterns.
8. Based on findings, take remediation action: trigger a re-index of the specific document, correct the ingestion pipeline error, or remove the incorrect moderation suppression. Verify the document appears in search results after remediation.

## Validation

- `GET /<index-name>/_doc/<document-id>` returns the document with `found: true`
- The representative query now returns the previously missing document in the expected position
- No error events for this document ID appear in the ingestion pipeline logs after remediation

## Rollback

1. If remediation actions unintentionally removed other documents or changed result ordering, identify the specific change made (e.g., moderation rule removal, field update).
2. Revert the specific change and re-validate that the original missing content issue is still present.
3. Escalate to Platform Lead with full investigation findings before attempting a second remediation.
