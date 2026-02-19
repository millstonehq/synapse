---
id: STANDARD-028
type: standard
title: Search Relevance Scoring Standard
status: deprecated
owner: Head of Engineering
created: '2024-01-30T10:47:03.238Z'
updated: '2026-07-10T18:53:33.943Z'
tags:
  - standard
  - search-platform
summary: Search Relevance Scoring Standard
related_policies:
  - POLICY-023
  - POLICY-021
example: true
related_systems:
  - SYSTEM-025
  - SYSTEM-022
---

## Area

This standard defines the requirements for how relevance scores are computed, normalized, and surfaced in search results across the Search Platform. It covers BM25 base scoring configuration, field weight assignments, function score boosting rules, and the minimum benchmarks that scoring configurations must meet before deployment to production.

## Controls

- The base similarity algorithm must be BM25 with documented `k1` and `b` parameter values; TF-IDF is not permitted for new indexes
- Field boost multipliers must be defined in a configuration file under version control; inline boost values in query DSL are not permitted in production
- Function score boosts applied to recency, popularity, or user signals must not exceed a multiplier of 3.0 over the base BM25 score without an approved exception
- All scoring configuration changes must pass the Search Relevance Evaluation benchmark with an NDCG@10 score no lower than the current production baseline
- Explain output (`explain: true`) must be enabled in staging query logs for at least 1% of queries to support ongoing relevance debugging
- Relevance benchmarks must be re-run and documented in the deployment change ticket for every scoring model update

## Compliance Mappings

- ISO/IEC 25010: Functional Suitability - Accuracy characteristic for information retrieval systems
- Internal Quality Gate: Search Relevance scorecard minimum 3.5/5 before production promotion

## Related Policies

- [[POLICY-023|Search Query Logging Policy]]
- [[POLICY-021|Search Data Indexing Policy]]
