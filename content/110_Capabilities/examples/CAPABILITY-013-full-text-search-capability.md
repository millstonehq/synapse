---
id: CAPABILITY-013
type: capability
title: Full-Text Search Capability
status: accepted
owner: VP Engineering
created: '2025-11-30T02:23:22.139Z'
updated: '2026-09-11T21:10:57.524Z'
tags:
  - capability
  - search-platform
summary: Full-Text Search Capability
evidence_links:
  - POLICY-021
  - STANDARD-026
  - STANDARD-030
example: true
---

## Domain

- Search Platform
- Content Discovery
- Information Retrieval

## Maturity (0-5)

**Current score: 4 / 5 (Managed)**

- **Level 0 - Initial**: No structured search capability. Users rely on browser find-in-page or manual navigation to locate content.
- **Level 1 - Ad hoc**: A basic keyword search exists but uses simple substring matching with no relevance ranking. Results are unsorted or sorted only by date.
- **Level 2 - Repeatable**: Full-text search backed by an inverted index (Elasticsearch/OpenSearch). BM25 relevance ranking applied. Field-level boosting configured for title vs. body. Results are deterministic for the same query.
- **Level 3 - Defined**: Formal analyzer chains are defined per content type and language. Index templates and mappings are version-controlled. Reindex procedures are documented. Query latency SLOs are defined and monitored.
- **Level 4 - Managed** (current): Query latency, zero-result rate, and NDCG@10 are tracked in a real-time dashboard. Automated canary evaluation gates new analyzer configurations before promotion. Index alias pattern enables zero-downtime reindexing. Synonym dictionaries are maintained with a quarterly review cadence.
- **Level 5 - Optimizing**: Continuous relevance improvement via online learning from click signals. Automated A/B testing framework for ranking model changes. Zero-result rate drives automated content gap alerts to the content team.

**Gap to Level 5**: Need to implement the online learning pipeline that feeds click signal data directly into ranking model retraining without manual intervention. Also need automated A/B test infrastructure for ranking experiments.

## Metrics

- Query P95 latency: Currently 320ms, target < 200ms
- Zero-result rate: Currently 4.2%, target < 3%
- NDCG@10 (weekly): Currently 0.74, target > 0.80
- Index freshness (time from publish to searchable): Currently 8s median, target < 10s
- Search availability: Currently 99.95%, target 99.9% (exceeding target)
- Synonym dictionary coverage: 1,240 terms across 8 domain groups

## Evidence Links

- [[POLICY-021|Search Data Governance Policy]] - Mandates data minimization and retention limits for search indices
- [[STANDARD-026|Search API Design Standard]] - Defines interface contracts and error response formats for search endpoints
- [[STANDARD-030|Search Index Quality Standard]] - Specifies required analyzer configurations, field mappings, and NDCG@10 thresholds for production promotion

## Notes

The capability advanced from Level 3 to Level 4 in Q2 2025 when the analytics dashboard (PRD-024) went live and automated index promotion gates were implemented.

Key improvements needed for Level 5:
- Implement online learning loop: click events from the analytics pipeline should trigger weekly LightGBM model retraining without manual engineer involvement
- Build A/B testing framework for ranking model changes (canary allocation, statistical significance testing, automatic rollback on degradation)
- Automate zero-result rate monitoring to generate Jira tickets for the content team when new high-volume zero-result query terms are detected
