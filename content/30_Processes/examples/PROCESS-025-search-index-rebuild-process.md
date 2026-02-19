---
id: PROCESS-025
type: process
title: Search Index Rebuild Process
status: review
owner: Platform Lead
created: '2024-03-21T13:12:41.330Z'
updated: '2026-02-08T15:54:15.133Z'
tags:
  - process
  - search-platform
summary: Search Index Rebuild Process
related_standards:
  - STANDARD-028
  - STANDARD-025
related_sops:
  - SOP-043
  - SOP-041
related_systems:
  - SYSTEM-021
example: true
---

## Purpose

The Search Index Rebuild Process ensures that the primary search index can be fully reconstructed from source data in a controlled, verifiable manner. This process is triggered when index corruption is detected, when a breaking schema change requires a full reindex, or when relevance improvements require re-analysis of all existing documents.

This process protects against data loss by building and validating the new index before switching production traffic, minimizing user impact during what would otherwise be a disruptive maintenance operation.

## Scope

- Full reindexing of production Elasticsearch indexes from canonical source systems
- Alias swap operations that redirect query traffic from an old index to a newly built index
- Schema migration rebuilds triggered by breaking mapping changes under [[STANDARD-028|Search Relevance Scoring Standard]]
- Partial rebuilds targeting specific document types or date ranges

## Roles and Responsibilities

- **Search Platform Engineer**: Initiates and monitors the rebuild job, validates index quality before alias swap
- **SRE On-Call**: Monitors cluster resource utilization during rebuild and authorizes alias swap
- **Platform Lead**: Approves the rebuild plan for full reindexes that will exceed 4 hours of run time
- **Data Engineering**: Provides confirmation that source data pipeline is healthy before rebuild begins

## Triggers

- Index corruption detected via shard health check or document count anomaly
- Breaking schema change approved and ready for deployment
- Quarterly relevance baseline refresh required by [[STANDARD-025|Search API Response Format Standard]] compliance review

## Inputs

- Approved rebuild plan with estimated document count, expected duration, and rollback criteria
- Current production index name and alias configuration
- Source data pipeline health confirmation from Data Engineering

## Outputs

- New index populated with all documents, validated against document count and relevance benchmark
- Alias updated to point to the new index
- Old index retained for 48 hours before deletion as rollback safety net

## Steps

1. Create the new target index with the updated mapping definition and verify the mapping is applied correctly
2. Disable auto-refresh on the new index (`refresh_interval: -1`) to maximize indexing throughput during the rebuild
3. Start the reindex job using the bulk indexing pipeline, setting throttle to 60% of cluster write capacity to preserve query performance
4. Monitor reindex progress every 30 minutes: check document count, indexing rate, and cluster CPU/memory
5. Once reindexing completes, re-enable refresh (`refresh_interval: 1s`) and force a final segment merge
6. Run the relevance benchmark suite against the new index via the staging alias and compare NDCG@10 against the production baseline
7. If benchmark passes, execute the alias swap: atomically remove the old index from the alias and add the new index
8. Monitor query error rate and latency for 15 minutes post-swap; roll back alias if SLOs degrade

## Controls

- Reindex jobs must not consume more than 60% of cluster write capacity to protect query SLOs
- Alias swaps require SRE On-Call acknowledgment before execution
- Relevance benchmark must pass before any alias swap is permitted
- Old indexes are retained 48 hours post-swap before deletion to support rollback
