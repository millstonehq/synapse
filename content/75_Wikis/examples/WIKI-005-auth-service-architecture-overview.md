---
id: WIKI-005
type: wiki
title: Auth Service - Architecture Overview
status: review
owner: User Team
created: '2024-06-09T22:46:13.166Z'
updated: '2025-10-15T01:45:51.686Z'
tags:
  - wiki
  - user-authentication
summary: Auth Service - Architecture Overview
source_repo: https://git.example.com/acme/auth-service
commit_sha: a9f9d8a82c4e666ba59a5a5c183a67cbcdbd8785
generated_at: '2026-03-20T08:56:04.306Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: medium
example: true
---

## Overview

The Auth Service is the central authentication and session orchestration layer for the platform. It coordinates the identity verification pipeline: credential validation, MFA challenge routing, session creation, and token issuance. The service acts as a facade over the underlying specialized services (OAuth Authorization Server, MFA Gateway, Session Management, User Directory).

This wiki was auto-generated from the `auth-service` repository. It reflects the service structure as of the commit listed in the frontmatter. For operational guidance, refer to the relevant runbooks in the Runbooks section.

## Architecture

The service is organized into four logical layers:

- **Handler Layer** (`internal/handler`): HTTP and gRPC request handlers. Handles request deserialization, input validation, context propagation, and response serialization. Each handler is thin — business logic is delegated to the use case layer.
- **Use Case Layer** (`internal/usecase`): Orchestration logic for authentication flows. The `LoginUseCase` coordinates credential validation, MFA challenge issuance, and session creation. The `TokenUseCase` delegates to the OAuth Authorization Server for token issuance.
- **Client Layer** (`internal/client`): Generated gRPC clients for downstream services (User Directory, MFA Gateway, Session Management, OAuth Server). Each client wraps the generated stubs with retry logic and circuit breakers.
- **Config Layer** (`internal/config`): Environment-driven configuration for service endpoints, TLS certificates, timeout budgets, and feature flags.

## Key Components

- **`LoginUseCase`**: The primary entry point for password-based authentication. Validates credentials against the User Directory, triggers MFA if enrolled, and hands off to `SessionUseCase` on success.
- **`OAuthUseCase`**: Handles authorization code flow initiation and callback processing. Validates PKCE parameters and delegates token issuance to the OAuth Authorization Server.
- **`SessionUseCase`**: Creates, validates, and terminates sessions by calling the Session Management Service. Also handles session refresh and concurrent session enforcement.
- **Circuit Breakers**: Each downstream client uses a circuit breaker (gobreaker) with a 5-failure threshold over 30 seconds and a 60-second recovery window.

## Configuration

| Config Key | Default | Description |
|-----------|---------|-------------|
| `USER_DIRECTORY_URL` | — | gRPC endpoint for User Directory Service |
| `MFA_GATEWAY_URL` | — | gRPC endpoint for MFA Gateway Service |
| `SESSION_SERVICE_URL` | — | gRPC endpoint for Session Management Service |
| `OAUTH_SERVER_URL` | — | HTTP endpoint for OAuth Authorization Server |
| `LOGIN_RATE_LIMIT` | 10/min | Per-IP rate limit for login attempts |
| `SESSION_TIMEOUT_HOURS` | 8 | Default session absolute timeout |

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `google.golang.org/grpc` | v1.61.0 | gRPC client transport |
| `github.com/sony/gobreaker/v2` | v2.0.0 | Circuit breaker for downstream calls |
| `golang.org/x/time` | v0.5.0 | Token bucket rate limiting |
| `github.com/prometheus/client_golang` | v1.18.0 | Metrics instrumentation |

## Generation Notes

Generated from commit `a9f9d8a` on the `main` branch. The generator analyzed Go source files, extracted package structure, interface definitions, and struct fields to produce this overview. Manual review is recommended for accuracy on internal business logic.
