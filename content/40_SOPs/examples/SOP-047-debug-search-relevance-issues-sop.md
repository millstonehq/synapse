---
id: SOP-047
type: sop
title: Debug Search Relevance Issues SOP
status: approved
owner: DevOps Lead
created: '2024-06-26T00:51:24.237Z'
updated: '2026-03-11T21:16:56.796Z'
tags:
  - sop
  - search-platform
summary: Debug Search Relevance Issues SOP
related_process: PROCESS-026
related_systems:
  - SYSTEM-022
example: true
---

## Preconditions

- A specific query or set of queries has been identified as producing poor results (e.g., expected documents not in top results, irrelevant documents appearing first)
- You have the exact query string(s) that are producing unexpected results
- You have access to the Elasticsearch cluster's query APIs and explain functionality

## Materials/Access

- Elasticsearch query console access for the production cluster (read-only is sufficient for diagnosis)
- The Explain API endpoint: `POST /<index-name>/_explain/<doc-id>`
- The Search API with explain enabled: `POST /<index-name>/_search` with `"explain": true`
- Access to the ranking configuration repository to review current field weights and boost functions
- Kibana Discover or equivalent for ad-hoc query exploration

## Procedure

1. Reproduce the issue: run the reported query in Kibana or via the Search API and confirm you see the unexpected results. Record the query string, the unexpected top results, and the expected but missing results.
2. Use the Explain API to understand why an expected document is not ranking higher: `POST /<index-name>/_explain/<expected-doc-id>` with the query body. Review the score breakdown — look at field-level BM25 contributions and any function score modifiers.
3. Run the query with `explain: true` on the top-ranked unexpected result to understand why it scores higher than expected. Compare the explain output from steps 2 and 3 to identify the scoring differential.
4. Check if the issue is in text analysis: use `POST /<index-name>/_analyze` with the query terms to see how the analyzer tokenizes the input. Compare against how the expected document's relevant fields were tokenized at index time.
5. Verify the index mapping for the fields involved: `GET /<index-name>/_mapping`. Confirm that the fields the query is searching are mapped as the expected type (text vs. keyword) with the intended analyzer.
6. Check the current ranking configuration for function score boosts that may be heavily overriding BM25 scores. High recency or popularity boosts can cause recently updated or frequently clicked documents to outrank more textually relevant ones.
7. If the issue is in field weights, simulate the fix: test a modified query with adjusted field boost values (`"fields": ["title^3", "body^1"]`) against the same query to verify the expected document rises in rank.
8. Document the root cause and proposed fix. If the fix requires a ranking configuration change, follow the Search Algorithm Update Process for the change to go through proper evaluation before production deployment.

## Validation

- The Explain API output confirms the root cause is understood (field weight imbalance, analyzer mismatch, or boost override)
- A modified test query with the proposed fix produces the expected ranking for the reported query set
- The proposed fix has been tested against the offline evaluation benchmark and does not regress other query types

## Rollback

1. If a quick-fix configuration change was applied directly to production to address an urgent relevance regression, revert it using the ranking configuration rollback procedure in the Deploy Search Ranking Update SOP.
2. Document the quick-fix scope and ensure a proper evaluation is scheduled within 5 business days.
