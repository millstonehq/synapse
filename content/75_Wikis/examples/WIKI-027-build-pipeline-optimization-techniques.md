---
id: WIKI-027
type: wiki
title: Build Pipeline - Optimization Techniques
status: review
owner: CI/CD Team
created: '2025-11-12T00:35:06.291Z'
updated: '2025-02-14T10:14:00.081Z'
tags:
  - wiki
  - ci-cd-platform
summary: Build Pipeline - Optimization Techniques
source_repo: https://git.example.com/acme/build-pipeline
commit_sha: 967590da4b88d3da703a53b7c85edddb2f8a7332
generated_at: '2025-10-31T05:37:42.823Z'
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

Build pipeline performance directly affects developer velocity. A slow pipeline delays feedback loops, discourages frequent commits, and increases the blast radius of any given change. This wiki documents the techniques applied to the CI/CD platform to reduce build times and improve throughput.

Current baseline: average build time 11.2 minutes across all services. Target: < 8 minutes for 90% of builds. Several high-impact optimizations are in progress or recently completed.

## Architecture

The pipeline is composed of sequential stages run by ephemeral Kubernetes runner pods. The critical path for most services is: dependency install → compile → unit tests → integration tests → Docker build → push artifact. Parallelism within stages and caching between stages are the two primary levers for reducing wall-clock time.

## Key Components

### Layer Ordering in Dockerfiles

The most common cause of Docker cache misses is incorrect layer ordering. Dependency install layers should always precede application code layers so that a code change does not invalidate the (expensive) dependency cache:

```dockerfile
# Correct - dependencies cached independently of source changes
COPY package.json package-lock.json ./
RUN npm ci
COPY src/ ./src/
RUN npm run build
```

### Build Cache Service

A distributed build cache keyed by content hash is used to share intermediate build outputs between runners. Cache hits are tracked per service per week; a hit rate below 60% triggers an investigation.

### Test Parallelism

Unit tests are sharded across 4 runner pods using `--shard` flags. Integration tests run sequentially per service to avoid shared-state collisions, but each service's integration suite runs concurrently with other services.

## Configuration

Key tunables for pipeline performance:

| Setting | Default | Notes |
|---------|---------|-------|
| `CACHE_TTL_DAYS` | 7 | Days before a cache key expires |
| `TEST_SHARD_COUNT` | 4 | Number of parallel test shards |
| `DOCKER_BUILDKIT` | 1 | Enables BuildKit for parallel Dockerfile stages |
| `MAX_CONCURRENT_JOBS_PER_REPO` | 3 | Prevents one active repo from starving others |

## Dependencies

- CI Runner Fleet Manager — provides runner pods for job execution
- Artifact Registry — receives final build outputs on job completion
- Docker BuildKit — in-daemon layer caching for container image builds
