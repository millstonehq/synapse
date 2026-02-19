---
id: GUIDE-008
type: guide
title: Authentication Service Local Development Guide
status: accepted
owner: Engineering Team
created: '2024-06-28T10:25:44.176Z'
updated: '2025-07-13T17:18:50.030Z'
tags:
  - guide
  - user-authentication
summary: Authentication Service Local Development Guide
audience: internal
related_systems:
  - SYSTEM-006
  - SYSTEM-007
related_sops:
  - SOP-019
  - SOP-020
example: true
---

## Why Local Development Matters

The authentication service is the critical path for every user login. Developing and testing auth changes locally before they reach staging prevents costly incidents and reduces the feedback loop. This guide walks you through getting the auth service running locally so you can develop against a real authentication stack rather than mocks.

## Prerequisites

You need the following installed: Docker and Docker Compose, Node.js 20+, and access to the internal npm registry. Clone the auth service repository: `git clone https://git.example.com/acme/auth-service`. Copy the example environment file: `cp .env.example .env.local` and fill in the required values (local keys are pre-configured in the example file; do not use production keys locally).

## Starting the Local Stack

The auth service uses Docker Compose to run its dependencies (Redis, a local Postgres instance, and a mock SMTP server for email OTPs):

```
docker compose -f docker-compose.dev.yml up -d
npm install
npm run db:migrate
npm run dev
```

The auth service will start on `http://localhost:3001`. The OIDC discovery document is available at `http://localhost:3001/.well-known/openid-configuration`.

For local JWT signing, the dev environment uses a pre-generated RSA key pair in `./dev-keys/`. These keys are for development only and must never be used in any shared environment.

## Testing Authentication Flows Locally

The local stack includes a set of seeded test users in `./seeds/dev-users.json`. Use these accounts to test different scenarios:

- Standard user login: `test-user@example.com` / `DevPassword123!`
- MFA-enrolled user: `mfa-user@example.com` / `DevPassword123!` (TOTP secret: `JBSWY3DPEHPK3PXP`)
- Locked account: `locked-user@example.com`
- Admin user: `admin@example.com` / `DevAdmin456!`

The local SMTP mock captures all outgoing emails at `http://localhost:8025` — useful for testing email OTP and password reset flows without a real email provider.

## Common Local Development Issues

If you see `JWKS key not found` errors from a downstream service consuming your local auth tokens, the downstream service is likely pointing at the production JWKS endpoint and cannot find your local dev key. Set `AUTH_JWKS_URL=http://localhost:3001/.well-known/jwks.json` in your downstream service's local configuration.

If Redis connection errors appear on startup, confirm Docker Compose finished starting before running the auth service: `docker compose ps` should show all containers as "running".
