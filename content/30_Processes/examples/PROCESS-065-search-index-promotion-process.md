---
id: PROCESS-065
type: process
title: Search Index Promotion Process
status: accepted
owner: Platform Lead
created: '2025-03-13T01:18:55.049Z'
updated: '2025-12-26T18:35:03.790Z'
tags:
  - process
  - search-platform
summary: Search Index Promotion Process
related_standards:
  - STANDARD-026
  - STANDARD-025
related_sops:
  - SOP-041
  - SOP-042
related_systems:
  - SYSTEM-021
example: true
---

## Purpose

Define the process for promoting a new or rebuilt Elasticsearch index to production search traffic. Index promotions are required for: new index mapping versions (field additions, analyzer changes), full corpus reindexes triggered by relevance model changes, and bulk document schema migrations. This process ensures zero search downtime, provides a rollback path, and maintains compliance with [[STANDARD-026|STANDARD-026]] (Search API Design Standard) and [[STANDARD-025|STANDARD-025]] (Search Data Handling Standard).

## Scope

All changes to the production Elasticsearch index that require switching the read alias (`search-content-read`) or write alias (`search-content-write`) to point at a new index. This includes:

- Index mapping version upgrades (adding or modifying field types, analyzers, or boost configurations)
- Full corpus reindexes (triggered by relevance model changes requiring re-embedding or re-enrichment)
- Language analyzer configuration updates
- Index template changes that require migration of existing documents

**Out of scope:** Incremental document updates processed by the indexing pipeline in the normal course of operations, and changes to the OpenSearch analytics indices (governed by a separate process).

## Roles and Responsibilities

- **Index Owner** - The Search Platform engineer who initiated the index change. Responsible for: creating the new index, running the bulk reindex job, validating quality gates, executing the alias swap, and monitoring post-promotion.
- **Search Platform Tech Lead** - Approver for all index promotions. Responsible for: reviewing the quality gate results before the alias swap, approving the maintenance window, and being available for rollback decisions.
- **On-Call Engineer** - The engineer on rotation during the promotion. Responsible for: monitoring search error rates and query latency during and after the alias swap.
- **QA Lead** - Optional for standard promotions; required for promotions that change the search result ranking algorithm. Responsible for: running the pre-promotion search quality regression test suite.

## Triggers

- A new Elasticsearch index mapping version is ready for production
- A relevance model change (LightGBM model update, field boost reconfiguration) requires a full reindex to take effect
- A synonym dictionary update requires documents to be reanalyzed with the new analyzer chain
- A compliance-driven bulk update is required (e.g., retroactive PII field redaction per [[STANDARD-025|STANDARD-025]])

## Inputs

- New index created and populated (document count within 0.5% of production index count)
- Quality gate results: NDCG@10 >= production baseline - 0.01 (no statistically significant regression)
- Approved change ticket
- For ranking changes: QA Lead sign-off on search quality regression test results
- For mapping changes affecting the query interface: [[STANDARD-026|STANDARD-026]] compliance review confirming no breaking changes to the search API response schema

## Outputs

- Production read alias (`search-content-read`) pointing at the new index
- Production write alias (`search-content-write`) pointing at the new index
- Old index retained for 48 hours as rollback target, then deleted
- Change ticket closed with promotion evidence (index name, alias swap timestamp, document count before and after)
- Post-promotion monitoring report (24-hour period after promotion)

## Steps

1. **Index Owner** creates the new index using the updated index template and verifies the mapping is correct: `GET /search-content-v{N}/_mapping`.
2. **Index Owner** runs the bulk reindex job (see [[SOP-041|SOP-041]] for the procedure). The reindex job reads all documents from the current production index and writes them to the new index, applying the new analyzer chain and any enrichment transformations.
3. **Index Owner** verifies document count parity: `GET /search-content-v{N}/_count` must be within 0.5% of the current production index count. Investigate any discrepancy before proceeding.
4. **Index Owner** runs the quality gate evaluation: execute the offline NDCG@10 evaluation script against the new index using the held-out query test set. The result must be >= (production baseline NDCG@10 - 0.01). Document the result in the change ticket.
5. **QA Lead** (if required) runs the search quality regression test suite: 200 hand-judged queries with expected top-3 results. Failures above a 5% threshold block the promotion.
6. **Search Platform Tech Lead** reviews quality gate results and approves the promotion, specifying the maintenance window (low-traffic period, typically between 02:00 and 05:00 local time).
7. **Index Owner** announces the promotion in #search-incidents and confirms the on-call engineer is monitoring.
8. **Index Owner** updates the write alias to point at the new index first: `POST /_aliases` with `remove` (old index, write alias) and `add` (new index, write alias) in a single atomic operation. This stops new documents from being written to the old index.
9. **Index Owner** updates the read alias to point at the new index (see [[SOP-042|SOP-042]] for the exact alias swap commands). This is the moment production search queries begin using the new index.
10. **On-Call Engineer** and **Index Owner** monitor for 15 minutes post-swap: search error rate must remain < 0.1%, P95 latency must remain < 200ms. If either threshold is breached, initiate rollback immediately (see Rollback section below).
11. **Index Owner** verifies the [[SYSTEM-021|Search Query Processing Service]] is returning results from the new index by checking the `_index` field in a sample search response.
12. **Index Owner** marks the change ticket complete and schedules old index deletion for 48 hours later.

## Rollback

If quality issues are detected after the alias swap:

1. Immediately swap the read alias back to the old index: `POST /_aliases` with the old index name.
2. Swap the write alias back to the old index.
3. Post to #search-incidents with the rollback reason and timestamp.
4. Do not delete the old index until root cause is understood.
5. Open a post-mortem investigation ticket.

The rollback must complete within 5 minutes of the decision to roll back. The Index Owner is responsible for executing the rollback even if the Tech Lead is unavailable.

## Controls

- No read alias swap without Tech Lead approval and a documented quality gate result
- Alias swaps must be executed during approved maintenance windows only (except emergency rollbacks)
- Old index must be retained for at least 48 hours post-promotion as rollback target
- All index promotions are logged in the change management system per [[STANDARD-025|STANDARD-025]] data traceability requirements
- NDCG@10 quality gate is a hard gate — promotions that fail the gate are blocked until the root cause is resolved
- Index template changes that add new fields used in the query API must be reviewed against [[STANDARD-026|STANDARD-026]] before the quality gate step
