---
id: GUIDE-067
type: guide
title: Optimizing Docker Build Cache Guide
status: accepted
owner: Engineering Team
created: '2025-04-22T21:49:22.407Z'
updated: '2025-07-20T13:00:02.302Z'
tags:
  - guide
  - ci-cd-platform
summary: Optimizing Docker Build Cache Guide
audience: partner
related_systems:
  - SYSTEM-035
  - SYSTEM-033
related_sops:
  - SOP-068
  - SOP-065
example: true
---

## Why This Matters

CI build time is a direct multiplier on developer feedback loops. When builds take 15 minutes, developers context-switch while waiting, stacking up uncommitted changes or moving on to other tasks. When builds take 3 minutes, developers stay in flow. Docker layer caching is the highest-leverage technique for reducing CI build time because most builds are incremental: only application code changes between commits, not OS packages or dependencies.

This guide covers the practical techniques for structuring Dockerfiles and CI configurations to maximize cache hit rate. The Build Performance Dashboard (see [[SYSTEM-035|SYSTEM-035]]) shows cache hit rates per service; use it to verify whether these techniques are having the expected effect after implementation.

## Prerequisites

Before applying cache optimizations, make sure you understand:

- How Docker's layer cache works: each Dockerfile instruction produces a layer; a cache miss on any layer invalidates all subsequent layers
- That the Build Cache Service provides a shared layer cache across all CI runners, so a cache-warm build on one runner benefits others
- That the `COPY` instruction is the most common source of unnecessary cache misses because it invalidates the cache when any copied file changes

## Dockerfile Layer Ordering

The most impactful single change is ordering Dockerfile instructions from least-frequently-changed to most-frequently-changed:

1. Base OS image and system packages (`apt-get install`) — changes only when the base image is updated; should be cached for weeks
2. Dependency file copy and install (`COPY go.mod go.sum ./ && RUN go mod download`) — changes only when dependencies change; should be cached for days
3. Application source copy and build (`COPY . . && RUN go build`) — changes on every commit; always a cache miss

A common anti-pattern is `COPY . .` early in the Dockerfile, which invalidates the dependency install layer on every commit. Split this into two steps: copy only the lockfile first, run the install, then copy the rest of the source.

## Build Cache Service Integration

The platform's Build Cache Service acts as a registry mirror for all CI runner layer pulls. CI runners are pre-configured to use it automatically via Docker's `--build-arg BUILDKIT_INLINE_CACHE=1` flag and a configured registry mirror. You do not need to change your Dockerfile to benefit.

To verify the cache is being used, check the build log for lines like `CACHED [stage-name ...]`. If you see `CACHED` for the dependency install layer, the cache is working. If all layers show as uncached, check the build log for `cache miss: content hash changed` messages and identify which instruction is causing unnecessary invalidation.

## Multi-Stage Build Best Practices

Multi-stage builds reduce final image size and can improve cache efficiency by separating the build environment from the runtime image:

- Use a named build stage: `FROM golang:1.21 AS builder`
- The build stage accumulates all dependencies and build tools; the runtime stage copies only the compiled binary
- Each stage has its own cache; changes to runtime-stage instructions don't invalidate builder-stage cache
- Pin the base image tag to a specific digest to prevent unexpected cache invalidation from upstream image updates

## Monitoring and Verification

After applying cache optimizations, verify the improvement using the Build Performance Dashboard:

- Navigate to your service in the [[SYSTEM-035|SYSTEM-035]] (Release Dashboard Service) build performance view
- Look at the "Cache Hit Rate" sparkline for your service over the last 7 days
- Compare the P95 build time before and after using the comparison view with the date you pushed the Dockerfile changes
- If cache hit rate is below 60%, re-examine the Dockerfile for early `COPY . .` instructions or dynamic layer content (timestamps, random values) that prevents caching

The [[SYSTEM-033|SYSTEM-033]] (Deployment Controller) build health section also surfaces services with unexpectedly slow build times as a leading indicator that cache configuration needs attention.
