---
id: WIKI-018
type: wiki
title: Elasticsearch Cluster - Configuration Guide
status: draft
owner: Search Team
created: '2024-02-15T17:58:43.010Z'
updated: '2026-01-25T23:21:13.710Z'
tags:
  - wiki
  - search-platform
summary: Elasticsearch Cluster - Configuration Guide
source_repo: https://git.example.com/acme/elasticsearch-cluster
commit_sha: 23648838a1a4f5c640cb517f5288601cf22df170
generated_at: '2025-05-29T21:45:17.240Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: high
example: true
---

## Overview

The production Elasticsearch cluster backing the Search Platform runs Elasticsearch 8.x across 5 nodes: 3 data nodes (hot tier) and 2 coordinating-only nodes. This page documents the cluster topology, key configuration settings, index template conventions, and operational guidelines for the Search Engineering team.

The cluster is deployed in AWS on `r6g.2xlarge` instances in 3 availability zones for fault tolerance. Index aliases separate the read and write paths to enable zero-downtime reindexing and blue/green index promotion.

## Architecture

**Node topology:**

- **Data nodes (3)**: Handle shard allocation, storage, and search execution. Each holds a primary shard and a replica of another node's primary. JVM heap set to 50% of instance RAM (cap at 31GB).
- **Coordinating nodes (2)**: Handle request routing, query fan-out, and result aggregation. No data stored; act as load balancers for the query layer. Memory optimized for aggregation workloads.
- **Master-eligible nodes**: All 3 data nodes are master-eligible. Minimum master nodes = 2 (split-brain protection).

**Index aliases:**

- `search-content-read` → points to the active read index
- `search-content-write` → points to the active write index (same as read during normal operations; diverges during reindexing)
- `search-suggestions` → single index, no alias swap needed

## Key Components

**Index template settings:**

```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "5s",
    "index.max_result_window": 10000,
    "index.mapping.total_fields.limit": 500
  }
}
```

**Analyzer chain** (default for text fields):
1. `standard` tokenizer
2. `lowercase` filter
3. `asciifolding` filter (diacritic normalization)
4. `stop` filter (English stopwords)
5. `synonym_graph` filter (loaded from synonym file)

**Cluster-level settings:**
- `cluster.routing.allocation.awareness.attributes: az` — ensures replica shards are placed in different AZs
- `indices.recovery.max_bytes_per_sec: 200mb` — throttle recovery to protect query performance

## Configuration

**JVM tuning (`jvm.options`):**

```
-Xms15g
-Xmx15g
-XX:+UseG1GC
-XX:G1HeapRegionSize=32m
-XX:+ExplicitGCInvokesConcurrent
```

**`elasticsearch.yml` (data nodes):**

```yaml
cluster.name: search-platform-prod
node.roles: [data, master]
network.host: 0.0.0.0
discovery.seed_hosts: ["es-data-1", "es-data-2", "es-data-3"]
cluster.initial_master_nodes: ["es-data-1", "es-data-2", "es-data-3"]
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
```

## Dependencies

| Component | Version | Notes |
|-----------|---------|-------|
| Elasticsearch | 8.12.x | Upgrade cadence: minor versions quarterly |
| Kibana | 8.12.x | Must match ES version exactly |
| JDK | Bundled JDK 21 | Do not replace with system JDK |
| AWS EBS (gp3) | 2TB per data node | IOPS provisioned at 6000, throughput 500MB/s |
