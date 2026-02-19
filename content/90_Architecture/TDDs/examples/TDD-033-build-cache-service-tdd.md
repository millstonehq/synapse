---
id: TDD-033
type: tdd
title: Build Cache Service TDD
status: draft
owner: Principal Engineer
created: '2025-10-22T12:00:46.283Z'
updated: '2025-01-23T17:41:34.476Z'
tags:
  - tdd
  - ci-cd-platform
summary: Build Cache Service TDD
related_adrs:
  - ADR-0026
  - ADR-0028
example: true
---

## Summary

Design the Build Cache Service, a centralized layer cache store for Docker image builds across all CI runner jobs. The service stores and serves individual image layer blobs keyed by content-addressed layer digests, enabling CI runners on different nodes to share cached layers without relying on each runner's local Docker daemon cache. The expected outcome is a reduction in average CI build time from 12 minutes to under 5 minutes by eliminating redundant base image and dependency layer downloads.

This design implements the build performance improvement objectives referenced in [[ADR-0026|ADR-0026]] and [[ADR-0028|ADR-0028]].

## Overview

- **Content-addressed storage**: Layers are stored by their SHA-256 digest, making deduplication automatic and cache invalidation unnecessary — any change to a layer produces a different digest and a new cache entry
- **Read-through proxy**: CI runners are configured to use the Build Cache Service as a registry mirror; cache misses transparently fetch from the upstream registry (Harbor or Docker Hub) and populate the cache
- **LRU eviction**: A background eviction job removes the least-recently-used layers when total cache size exceeds the configured high-water mark (default: 500 GB)
- **Cache hit telemetry**: Every request is recorded with hit/miss status, layer size, and requesting runner ID; metrics are exported to Prometheus for cache efficiency monitoring
- **No authentication barrier**: The service is internal-only and trusts requests from CI runner pod IPs; authentication is enforced at the network level via Kubernetes NetworkPolicy

## Architecture

- **Proxy Layer**: An OCI distribution-spec-compliant HTTP proxy fronting the cache store; handles `GET /v2/{name}/blobs/{digest}` requests and implements the pull-through logic
- **Cache Store**: Content-addressed blob storage backed by an S3-compatible object store (MinIO on-cluster); blob metadata (size, last-accessed, hit count) tracked in PostgreSQL
- **Eviction Controller**: Background goroutine that runs on a 1-hour interval; queries PostgreSQL for blobs exceeding the retention window and deletes them from S3 and the metadata table
- **Metrics Collector**: Prometheus `/metrics` endpoint exposing cache hit rate, total stored bytes, eviction counts, and P95 fetch latency for cache hits vs. misses
- **Upstream Client**: Pulls layers from Harbor or Docker Hub on cache misses, respects upstream registry auth, and streams layers to both the S3 store and the requesting client simultaneously

## Information Model

- **BlobRecord**: PostgreSQL row tracking `digest` (primary key), `size_bytes`, `last_accessed_at`, `hit_count`, `source_registry`, `created_at`
- **EvictionCandidate**: View joining BlobRecord with storage tier; used by the eviction controller to select blobs to remove based on LRU score
- **CacheStats**: Aggregated metrics struct exposed via the API and Prometheus endpoint; includes `total_blobs`, `total_bytes`, `hit_rate_7d`, `evictions_last_24h`
- **UpstreamConfig**: Per-registry configuration (URL, credentials, rate limits) loaded from Kubernetes Secrets at startup; determines where cache misses are fetched from

## Interfaces

- `GET /v2/{name}/blobs/{digest}` - OCI-compliant blob fetch; returns cached blob or fetches from upstream
- `HEAD /v2/{name}/blobs/{digest}` - Check blob existence without downloading
- `GET /v1/stats` - Cache hit rate, storage utilization, eviction summary
- `GET /healthz` - Liveness probe; verifies S3 and PostgreSQL connectivity
- `DELETE /v1/blobs/{digest}` - Admin endpoint to manually evict a specific blob (requires service account token)

## Files and Layout

```
cmd/build-cache/main.go         - Entry point, service initialization
internal/
  proxy/
    handler.go                  - OCI distribution spec HTTP handlers
    upstream.go                 - Pull-through fetch from upstream registries
  store/
    s3.go                       - S3-compatible blob read/write
    metadata.go                 - PostgreSQL blob metadata operations
  eviction/
    controller.go               - LRU eviction background job
  metrics/
    collector.go                - Prometheus metrics exporter
  config/
    upstream.go                 - Registry auth configuration loader
deploy/
  helm/                         - Helm chart for the cache service
migrations/                     - PostgreSQL schema for blob metadata
```

## Work Plan

1. **Phase 1 - Proxy Scaffold (Week 1-2)**: Implement OCI blob endpoint handlers; direct pass-through to Harbor with no caching; deploy to staging for integration testing
2. **Phase 2 - Cache Store (Week 3-4)**: Add S3 write-on-fetch and PostgreSQL metadata recording; implement cache-hit path returning stored blobs; basic hit/miss metrics
3. **Phase 3 - Eviction Controller (Week 5)**: Implement LRU eviction job; configure high-water mark; integration test with synthetic storage fill
4. **Phase 4 - CI Integration (Week 6)**: Update CI runner Dockerd configuration to use cache service as registry mirror; measure build time reduction in staging
5. **Phase 5 - Observability (Week 7)**: Grafana dashboard for cache efficiency; alert on cache hit rate below 60%; document tuning guide
6. **Phase 6 - Production Rollout (Week 8)**: Gradual rollout to production runners; monitor cache hit rate and S3 costs; tune eviction thresholds

## Risks and Mitigations

- **Risk**: Cache service unavailability blocks all CI builds if runners cannot fall back to upstream. **Mitigation**: Configure Docker's registry mirror setting with a fallback to the upstream registry; cache service failure is transparent to runners, with a latency penalty only.
- **Risk**: S3 storage grows unboundedly if eviction is misconfigured or too slow. **Mitigation**: Hard limit on S3 bucket size via bucket policy alert; eviction controller runs on 1-hour interval with alerting if it fails to run.
- **Risk**: Cache poisoning if a corrupt layer is stored. **Mitigation**: Verify SHA-256 digest of every layer on write; reject and re-fetch from upstream if digest mismatch is detected.
