---
id: ADR-0009
type: adr
title: Choose Redis for Session Storage
status: approved
owner: Staff Engineer
created: '2025-03-05T09:20:24.638Z'
updated: '2026-11-11T15:55:09.607Z'
tags:
  - adr
  - user-authentication
summary: Choose Redis for Session Storage
example: true
supersedes: ADR-0007
---

## Context

The Session Management Service requires a storage backend for active session tokens. Sessions must be lookupable by token (random string key), support TTL-based automatic expiry for absolute and sliding timeouts, and handle approximately 1,200 lookups per second at peak with sub-10ms P99 latency. The session store must also support the concurrent session limit feature, which requires atomic operations to count and cap active sessions per user.

The previous approach (ADR-0007) used PostgreSQL as the session store with a background job for TTL enforcement. This has proven inadequate at scale: the PostgreSQL approach has a measured P99 session lookup latency of 45ms (target: 10ms), and the background expiry job has a maximum 5-minute lag, meaning sessions live up to 5 minutes longer than intended. Additionally, the PostgreSQL session table has grown to 80 million rows and is now a performance hotspot.

We evaluated Redis, DynamoDB, and a purpose-built session service backed by the existing PostgreSQL cluster.

## Decision

We will use **Redis 7 Cluster mode** as the primary session store. Session tokens map to MessagePack-serialized session records with Redis TTL for automatic expiry. Sliding expiry is implemented by resetting the TTL on every validation call. Concurrent session limits are enforced using a Redis sorted set per user (sorted by creation timestamp) with atomic ZADD + ZCARD + ZPOPMIN operations.

Redis Cluster with 3 primary nodes and 3 replicas will be deployed in Kubernetes. This provides automatic failover (sub-30-second) without the 2-minute Sentinel failover window of the previous Redis Sentinel setup.

PostgreSQL is retained as an append-only audit log of session lifecycle events (created, refreshed, terminated) but is not in the hot path for session validation.

## Consequences

**Positive:**
- Sub-millisecond session lookups (Redis GET on hash key) vs. 45ms on PostgreSQL
- Native TTL enforcement eliminates the expiry lag problem; sessions expire precisely at their configured TTL
- Atomic sorted set operations for concurrent session limiting are simple and correct
- Redis Cluster mode eliminates the 2-minute Sentinel failover window from the previous implementation

**Negative:**
- Redis is an in-memory store; a full cluster failure with no replica promotion results in all active sessions being lost, requiring all users to re-authenticate
- Redis persistence (RDB/AOF) adds overhead; session data is considered ephemeral so we opt for no persistence, accepting the full-cluster-loss scenario
- Operational complexity of Redis Cluster is higher than standalone Redis or Sentinel

**Neutral:**
- Session audit data is preserved in PostgreSQL regardless of Redis state, satisfying compliance audit requirements
- Memory sizing must account for session record size times peak concurrent session count; at current scale, 3 nodes × 8GB provides ~5x headroom

## Alternatives Considered

**DynamoDB**:
- Pro: Managed service, no operational overhead, TTL natively supported, scales to any size
- Con: ~5-10ms read latency vs. <1ms for Redis; DynamoDB is a significant cost increase at our session volume; adds an AWS dependency to a service currently running on-premises
- Rejected because: Latency does not meet the 10ms P99 target; cost is prohibitive

**PostgreSQL with optimized indexes (extend current approach)**:
- Pro: No new infrastructure; simpler operationally
- Con: Fundamental latency ceiling for indexed row lookups under write-heavy load; TTL enforcement via background job is inherently laggy; scaling requires sharding which adds complexity
- Rejected because: Cannot meet the 10ms P99 latency target even with further optimization
