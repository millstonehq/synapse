---
id: SOP-041
type: sop
title: Rebuild Search Index from Scratch SOP
status: approved
owner: SRE Lead
created: '2024-02-07T18:02:01.783Z'
updated: '2026-10-24T03:06:32.054Z'
tags:
  - sop
  - search-platform
summary: Rebuild Search Index from Scratch SOP
related_process: PROCESS-029
related_systems:
  - SYSTEM-021
example: true
---

## Preconditions

- The source data pipeline is confirmed healthy by Data Engineering
- The target cluster has at least 50% free disk space to accommodate the new index alongside the existing one
- Cluster health is green; do not begin a scratch rebuild if any shards are unassigned
- A change ticket is approved with the justification for the full rebuild (e.g., schema change, corruption event)
- The new index mapping file is committed to version control and reviewed by the Platform Lead

## Materials/Access

- SSH or kubectl access to the Elasticsearch cluster management nodes
- Access to the bulk indexing pipeline control plane (Airflow or equivalent)
- Grafana dashboard: Search Cluster Overview (cluster health, node memory, indexing rate)
- The approved index mapping JSON file for the new index
- The alias name currently serving production traffic

## Procedure

1. Create the new index with the versioned name (e.g., `search-docs-v42`) using the approved mapping file: `PUT /search-docs-v42` with the mapping JSON body. Verify the mapping is applied by calling `GET /search-docs-v42/_mapping`.
2. Set `refresh_interval` to `-1` and `number_of_replicas` to `0` on the new index to maximize indexing throughput during the bulk load phase.
3. Trigger the bulk reindex job in the pipeline control plane, pointing it at the new index. Set throttle to 60% of cluster write capacity to preserve query performance on the existing index.
4. Monitor indexing progress every 30 minutes via Grafana: confirm indexing rate is steady and cluster CPU/memory headroom remains above 30%.
5. Once the pipeline reports completion, verify document count: `GET /search-docs-v42/_count`. Compare against the expected count from the source system. A deviation of more than 0.1% requires investigation before proceeding.
6. Re-enable refresh and replicas: set `refresh_interval: "1s"` and `number_of_replicas: 1`. Wait for replica shards to be fully allocated and cluster status to return to green.
7. Run the relevance benchmark suite against the new index using the staging alias. Confirm NDCG@10 meets or exceeds the production baseline. If it fails, do not proceed — investigate and resolve the gap.
8. Execute the alias swap atomically: `POST /_aliases` with actions to remove the old index and add the new index to the production alias. Confirm the alias now points to the new index.
9. Monitor query error rate and P95 latency for 15 minutes post-swap. If either degrades, immediately revert the alias to the old index.

## Validation

- `GET /_cat/aliases?v` shows the production alias pointing to the new index
- `GET /_cluster/health` returns status `green` with all shards allocated
- Query error rate and P95 latency are at or below pre-rebuild baselines after 15-minute monitoring window
- Document count on the new index matches source system count within 0.1%
- Relevance benchmark NDCG@10 meets or exceeds baseline

## Rollback

1. Post in #search-incidents: "Reverting alias swap for [index]. Reason: [brief description]."
2. Execute the alias revert: `POST /_aliases` with actions to remove the new index and add the old index back to the production alias.
3. Confirm `GET /_cat/aliases?v` shows the production alias pointing to the old index.
4. Verify query error rate and P95 latency return to pre-swap baselines within 5 minutes.
5. Retain the failed new index for at least 48 hours for post-incident analysis before deletion.
