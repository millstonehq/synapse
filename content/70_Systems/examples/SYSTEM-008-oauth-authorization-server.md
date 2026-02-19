---
id: SYSTEM-008
type: system
title: OAuth Authorization Server
status: approved
owner: User Engineering
owner_team: User Engineering
runtime: Kubernetes / Go 1.22 / ClickHouse / Kafka
created: '2024-05-13T10:15:14.582Z'
updated: '2025-07-07T08:02:13.270Z'
tags:
  - system
  - user-authentication
summary: OAuth Authorization Server
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/oauth-authorization-server
dependencies:
  - MFA Gateway Service
  - User Directory Service
runbooks:
  - RUNBOOK-012
  - RUNBOOK-013
example: true
---

## Overview

The OAuth Authorization Server implements the OAuth 2.1 authorization framework and OpenID Connect 1.0 for the platform. It issues access tokens, refresh tokens, and ID tokens to registered client applications and manages the authorization code flow, client credentials flow, and device authorization flow.

The server processes approximately 120,000 token issuance and validation requests per day. It integrates with the MFA Gateway Service to enforce step-up authentication during high-risk authorization requests and queries the User Directory Service for user profile and consent data.

## Architecture

The server is structured around the OAuth 2.1 grant type handlers and a central token store:

- **Authorization Endpoint**: Handles authorization requests, validates client identity, redirects users for consent, and issues authorization codes stored briefly in Redis.
- **Token Endpoint**: Exchanges authorization codes, refresh tokens, and client credentials for access tokens and ID tokens. Implements PKCE validation for public clients.
- **Token Introspection Endpoint**: Allows resource servers to validate opaque tokens and retrieve associated claims without parsing JWTs.
- **JWKS Endpoint**: Publishes the public keys used for JWT signing, rotated on a 90-day schedule with a 7-day overlap period.
- **Event Log**: All authorization events are published to Kafka for consumption by audit and analytics pipelines, stored in ClickHouse for long-term retention.

## Repositories

- [oauth-authorization-server](https://git.example.com/acme/oauth-authorization-server) - Application code, key management tooling, Helm chart

## Runtime Environment

- **Platform**: Kubernetes across 3 availability zones
- **Language**: Go 1.22
- **Replicas**: 4 pods minimum, autoscaling to 16 based on CPU and request rate
- **Resources**: 512Mi memory request / 1Gi limit, 500m CPU request / 1 CPU limit per pod
- **Deployment**: Blue-green via ArgoCD
- **Key Storage**: Signing keys stored in HashiCorp Vault, fetched at startup and cached in memory

## Dependencies

- Redis 7 — short-lived authorization code storage (TTL: 60 seconds), token blacklist
- ClickHouse — long-term authorization event analytics
- Kafka — authorization event streaming to downstream consumers
- MFA Gateway Service — step-up authentication challenges
- User Directory Service — user profile lookup and consent record storage

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Latency (token issuance) | P50 < 50ms, P99 < 200ms |
| Latency (token validation) | P50 < 10ms, P99 < 40ms |
| Error rate | < 0.1% 5xx responses |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-012|OAuth Server Token Endpoint Runbook]]
- [[RUNBOOK-013|OAuth Key Rotation Runbook]]
