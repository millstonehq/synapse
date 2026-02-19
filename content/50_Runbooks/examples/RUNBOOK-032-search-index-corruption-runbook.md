---
id: RUNBOOK-032
type: runbook
title: Search Index Corruption Runbook
status: approved
owner: On-Call Engineer
created: '2025-06-01T03:10:12.562Z'
updated: '2025-11-09T11:17:27.068Z'
tags:
  - runbook
  - search-platform
summary: Search Index Corruption Runbook
example: true
---

## Service

- **System**: [[SYSTEM-021|Search Cluster]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Elasticsearch 8 / NVMe-backed persistent volumes

## Alerts

- `search_index_corruption_detected` - Lucene checksum verification failure detected on one or more index segments
- `search_shard_failed` - A shard has transitioned to the FAILED state and cannot be recovered
- `search_document_count_anomaly` - Index document count has dropped by more than 5% without a corresponding delete operation in the ingestion pipeline

## Diagnosis Steps

1. **Identify the affected index and shard** - Run `GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason` and filter for shards in `UNASSIGNED` or `FAILED` state. Note the index name and shard numbers.
2. **Check Elasticsearch logs for corruption messages** - Search logs on the data nodes for `CorruptIndexException`, `ChecksumException`, or `file checksum mismatch` messages. These indicate Lucene segment file corruption on disk.
3. **Check storage health** - Verify the underlying persistent volume is healthy. Check for I/O errors in the node's kernel logs (`kubectl exec <pod> -- dmesg | grep -i error`). Corruption is often caused by disk hardware failure or volume detachment.
4. **Assess the scope** - Determine whether corruption affects a primary shard or a replica shard. Replica corruption is recoverable by deleting the replica and allowing Elasticsearch to re-replicate from the primary. Primary corruption is more severe.
5. **Check if a snapshot exists** - Run `GET /_snapshot` to list snapshot repositories, then `GET /_snapshot/<repo>/_all?verbose=false` to find the most recent snapshot for the affected index.

## Remediation Steps

1. **If only a replica shard is corrupted**: Cancel the failed replica and allow Elasticsearch to re-replicate: `POST /_cluster/reroute` with an `allocate_empty_primary` action is NOT used here — instead, delete and re-add the replica allocation via `PUT /<index>/_settings` with `number_of_replicas: 0` then restore to `1`.
2. **If a primary shard is corrupted and a replica is healthy**: Force-promote the healthy replica to primary by closing the index, running `POST /_cluster/reroute` with `allocate_stale_primary` (accepting data loss only if no other option), then reopen.
3. **If both primary and replica are corrupted**: Restore the affected shards from the most recent snapshot: `POST /<index>/_recovery` from snapshot or perform a full index restore followed by delta reindex from the ingestion pipeline for documents added after the snapshot.
4. **If corruption is caused by a failed disk**: Escalate to infrastructure on-call to replace the volume. Do not restart the affected pod on the same volume until the disk is replaced.
5. **After recovery**: Run `POST /<index>/_forcemerge?only_expunge_deletes=true` and verify `GET /<index>/_shard_stores` shows no corruption warnings.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms corruption and identifies scope |
| 10 min | Post status in #search-incidents; determine if search is serving degraded results |
| 20 min | Page Search Platform tech lead via PagerDuty |
| 40 min | If primary data loss is possible: page Engineering Manager immediately |
| 60 min | Escalate to Elasticsearch vendor support for severe corruption scenarios |

## Dashboards

- [Search Cluster Overview](https://grafana.example.com/d/search-cluster-overview) - Shard health, failed shard count
- [Search Index Health](https://grafana.example.com/d/search-index-health) - Document counts by index, shard store status
- [Kubernetes Storage](https://grafana.example.com/d/k8s-storage) - PVC health, I/O error rates
