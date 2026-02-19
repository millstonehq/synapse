---
id: RUNBOOK-020
type: runbook
title: Inventory Search Index Rebuild Runbook
status: draft
owner: On-Call Engineer
created: '2024-04-10T21:53:56.530Z'
updated: '2026-07-20T20:06:41.501Z'
tags:
  - runbook
  - inventory-management
summary: Inventory Search Index Rebuild Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `inventory_search_index_stale` - Search index last rebuild timestamp is more than 6 hours old
- `inventory_search_query_errors_high` - Search query error rate exceeds 5% for 3 minutes, often caused by a corrupt or missing index
- `inventory_search_index_rebuild_failed` - A scheduled or triggered index rebuild job has failed to complete
- `inventory_search_zero_results` - More than 20% of search queries are returning zero results (index likely missing or corrupt)

## Diagnosis Steps

1. **Check index rebuild job status** - Navigate to the Inventory Admin Portal > Jobs > Search Index Rebuild. Check the last completed job's status, duration, and error message if failed.
2. **Query index metadata** - Call `GET /admin/search/index/status` on the inventory search service. Note the last successful rebuild timestamp, total indexed records, and index health status.
3. **Compare index record count to database** - Compare the `total_indexed_records` from the index status to the count of active SKUs in the inventory database. A large gap indicates the index is significantly out of date or corrupt.
4. **Check search service pod health** - Run `kubectl get pods -n inventory -l app=inventory-search`. Look for pods in error states or with high restart counts.
5. **Check underlying storage** - If the search index uses Elasticsearch or a similar engine, check cluster health: green/yellow/red. A red cluster health indicates lost shards and will require infrastructure intervention.

## Remediation Steps

1. **If the index is stale but the rebuild job failed silently** - Check the search service logs for the failure reason. If it is a resource issue (OOM during rebuild), trigger the rebuild job during off-peak hours with increased memory limits.
2. **If search is returning high error rates due to a corrupt index** - Immediately trigger an emergency index rebuild: `POST /admin/search/index/rebuild`. This will cause elevated database read load during the rebuild (typically 20-40 minutes). Monitor database CPU during the rebuild.
3. **If the rebuild job itself is failing** - Check for disk space issues on the search index storage volume: `kubectl exec -n inventory -it [search-pod] -- df -h /data`. If disk is full, delete the corrupted index files and trigger a fresh rebuild.
4. **If the search cluster shows red health** - This is an infrastructure issue. Page the infrastructure on-call. Do not attempt to delete or restore shards independently.
5. **If search is unavailable and affecting order picking workflows** - Notify the Warehouse Operations Lead and enable fallback catalog lookup mode, which queries the database directly (slower but correct).

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks index status and last rebuild timestamp |
| 10 min | Post diagnosis and planned action in #inventory-incidents |
| 15 min | Trigger emergency rebuild if index is corrupt or missing |
| 30 min | If rebuild is not progressing or infrastructure issue: page infrastructure on-call |
| 60 min | If warehouse picking is impacted: escalate to Engineering Manager and Warehouse Operations Lead |

## Dashboards

- [Inventory Search](https://grafana.example.com/d/inventory-search) - Query rate, error rate, latency, index freshness
- [Inventory Search Index Jobs](https://grafana.example.com/d/inventory-index-jobs) - Rebuild job history, duration, record counts
- [Inventory Database](https://grafana.example.com/d/inventory-db) - Read load during index rebuild operations
- [Search Storage](https://grafana.example.com/d/search-storage) - Disk usage, I/O throughput for search index volumes
