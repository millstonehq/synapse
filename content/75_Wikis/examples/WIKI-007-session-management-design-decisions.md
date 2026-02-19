---
id: WIKI-007
type: wiki
title: Session Management - Design Decisions
status: review
owner: User Team
created: '2025-05-01T11:43:44.604Z'
updated: '2025-03-15T12:15:10.933Z'
tags:
  - wiki
  - user-authentication
summary: Session Management - Design Decisions
source_repo: https://git.example.com/acme/session-management
commit_sha: 8cab1516bf611a93ae42cca7b9b32caf6f68365b
generated_at: '2026-08-10T05:58:53.227Z'
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
importance: low
example: true
---

## Overview

This page documents the key design decisions made during the implementation of the Session Management Service. It explains the rationale for the opaque token approach, Redis as the primary store, sliding vs. absolute timeout policy, and concurrent session handling. These decisions are recorded here to provide context for future maintainers.

This page was auto-generated from repository analysis of the `session-management` repository. It reflects decisions encoded in the codebase as of the commit listed in the frontmatter.

## Architecture

The session store architecture centers on two data layers:

- **Redis (primary)**: Session tokens map to session metadata (user ID, created_at, last_accessed_at, device_fingerprint). Redis TTL enforces absolute session expiry. Sliding expiry is implemented by resetting the TTL on each validation call.
- **PostgreSQL (audit)**: Append-only `session_events` table records session creation, renewal, and termination events with timestamps and IP addresses. This data is never deleted and supports compliance audits.
- **No JWT sessions**: The team explicitly chose opaque random tokens over JWTs for sessions. JWTs cannot be revoked without a blocklist; opaque tokens can be deleted from Redis immediately on logout or administrative revocation.

## Key Components

- **`session.Store`** (`internal/store/redis.go`): The core interface for Redis session operations. Implements `Create`, `Get`, `Refresh`, `Delete`, and `DeleteAll` (purge all sessions for a user). Uses pipeline transactions for atomic create+audit operations.
- **`session.Policy`** (`internal/policy/policy.go`): Encapsulates timeout and concurrency rules. Supports per-user-tier policy overrides (e.g., admin accounts have 1-hour absolute timeout vs. 8 hours for standard users).
- **`concurrent.Limiter`** (`internal/concurrent/limiter.go`): Tracks active session count per user in a Redis sorted set (scored by creation time). When the limit is reached, the oldest session is evicted before the new one is created.

## Configuration

| Config Key | Default | Description |
|-----------|---------|-------------|
| `SESSION_ABSOLUTE_TTL_HOURS` | 8 | Maximum session lifetime regardless of activity |
| `SESSION_IDLE_TTL_MINUTES` | 30 | Inactivity timeout (sliding expiry) |
| `SESSION_MAX_CONCURRENT` | 5 | Maximum concurrent sessions per user |
| `REDIS_KEY_PREFIX` | `sess:` | Namespace prefix for all session keys |
| `AUDIT_ASYNC` | true | Write audit records asynchronously |

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `github.com/redis/go-redis/v9` | v9.3.0 | Redis session store |
| `github.com/jackc/pgx/v5` | v5.5.1 | PostgreSQL audit log |
| `go.uber.org/zap` | v1.27.0 | Structured logging |

## Generation Notes

Generated from commit `8cab151` on the `main` branch. The generator analyzed Go source files and extracted package structure and configuration constants. Manual review is recommended for policy configuration details.
