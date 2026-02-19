---
id: GUIDE-029
type: guide
title: Search Performance Optimization Guide
status: approved
owner: Engineering Team
created: '2024-01-23T11:24:09.546Z'
updated: '2026-12-16T12:49:47.700Z'
tags:
  - guide
  - search-platform
summary: Search Performance Optimization Guide
audience: customer
related_systems:
  - SYSTEM-023
  - SYSTEM-021
related_sops:
  - SOP-050
  - SOP-041
example: true
---

## Why Performance Matters

Search is a synchronous, user-facing operation. Users perceive latency above 200ms, and abandonment rates climb sharply above 500ms. Performance optimization in search has two dimensions: reducing per-query latency and ensuring the cluster has sufficient capacity to handle peak concurrent query volumes without saturation.

## Query-Level Optimizations

The single most impactful query optimization is reducing scope — fewer documents examined means faster results.

**Use filters for non-scoring criteria**: If a criterion does not affect relevance ranking (e.g., `status = published`), use a `filter` clause rather than a `must` clause. Filtered queries are cached by Elasticsearch's query cache, while scored queries are not.

**Avoid deep pagination**: Retrieving the 1,000th result (`from: 990, size: 10`) requires Elasticsearch to score and rank all preceding documents before discarding them. Use cursor-based pagination (search-after) for any pagination depth beyond 100 results.

**Limit highlighted fields**: Highlighting requires re-analyzing matched documents to find term positions. Request highlighting only for fields that are rendered in the UI and limit the number of fragments: `"number_of_fragments": 2, "fragment_size": 150`.

## Index-Level Optimizations

**Shard sizing**: Optimal shard size is 10-50GB. Very small shards (under 1GB) create overhead from shard-level coordination; very large shards (over 100GB) slow down query execution and segment merges. Right-size shards based on expected index data volume.

**Segment merging**: Many small segments slow queries because Elasticsearch must search each segment separately and merge results. Schedule force merges (`POST /<index>/_forcemerge?max_num_segments=5`) on read-heavy indexes during off-peak hours to consolidate segments.

**Field data loading**: Queries involving `sort` or aggregations on `text` fields require loading field data into memory at query time — this is slow. Pre-map such fields as `keyword` type to use doc values instead, which are loaded from disk at index time.

## Cluster-Level Optimizations

**JVM heap sizing**: Set Elasticsearch JVM heap to no more than 50% of available node RAM, up to a maximum of 32GB. Above 32GB, JVM pointer compression is disabled and performance degrades. The other 50% of RAM is used by the OS for filesystem cache, which significantly accelerates disk-based query operations.

**Thread pool configuration**: The default search thread pool size is `(CPU cores / 2) + 1`. For query-heavy workloads with many concurrent users, this is often too low. Monitor the `search` thread pool queue depth in Grafana; sustained queuing indicates the thread pool needs tuning or the cluster needs more nodes.

## Monitoring and Profiling

Use the Profile API (`"profile": true`) on slow queries to see exactly which phases are taking time. Common findings include expensive term frequency calculations in large nested queries and slow `script_score` functions. Profile data should never be collected in production at scale — use it on a targeted query in staging to diagnose specific slow query patterns.
