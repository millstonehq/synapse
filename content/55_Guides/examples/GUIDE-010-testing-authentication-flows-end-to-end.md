---
id: GUIDE-010
type: guide
title: Testing Authentication Flows End-to-End
status: deprecated
owner: Developer Experience
created: '2024-08-30T12:07:13.088Z'
updated: '2026-12-18T04:19:53.918Z'
tags:
  - guide
  - user-authentication
summary: Testing Authentication Flows End-to-End
audience: internal
related_systems:
  - SYSTEM-010
  - SYSTEM-006
related_sops:
  - SOP-014
  - SOP-013
example: true
---

## Why End-to-End Auth Testing Matters

Unit tests for authentication logic do not catch integration failures: token format mismatches between services, redirect URI misconfiguration, clock skew causing token rejections, or session state inconsistencies. End-to-end authentication tests exercise the complete flow from user credential submission through token issuance and validation at a resource server.

Without E2E auth tests, regressions in login, MFA challenges, and token refresh can reach production silently. This guide explains how to use our E2E test framework to cover authentication flows in your service.

## Setting Up the Test Environment

The E2E test suite uses a dedicated test identity provider instance (`auth-test.internal.example.com`) seeded with test accounts. Set up your service's E2E test environment with:

```
AUTH_ISSUER=https://auth-test.internal.example.com
AUTH_CLIENT_ID=your-service-test-client
AUTH_CLIENT_SECRET=<from CI secrets>
```

The test identity provider is isolated from production; test accounts and tokens issued here are not valid in production.

## Core Flows to Test

Every service that consumes authentication tokens should test the following flows:

**Happy path**: User logs in with valid credentials, completes MFA if enrolled, receives an access token, accesses a protected resource with the token, token expires, refresh succeeds, user can still access the resource.

**Rejection cases**: Expired access token with no refresh token is rejected with 401. Tampered token signature is rejected. Token with incorrect audience is rejected. Revoked refresh token returns 401 on the refresh endpoint.

**MFA scenarios**: Login requiring TOTP challenge completes correctly. Login with wrong TOTP code fails with clear error. Account with MFA enforcement cannot log in without completing MFA.

## Using the Auth Test Helpers

The `@internal/auth-test-helpers` package provides utilities for E2E tests:

```typescript
import { createTestUser, getTestToken, revokeTestToken } from '@internal/auth-test-helpers';

const user = await createTestUser({ roles: ['read:orders'] });
const token = await getTestToken(user.id);
// ... use token in test
await revokeTestToken(token);
```

Clean up test users and tokens after each test run to prevent test account accumulation in the test identity provider.

## Continuous Integration

Run authentication E2E tests in CI on every PR that touches authentication-related code, and nightly for all services to catch token format or JWKS changes that may have propagated. Use the `--auth-smoke` flag on the nightly run to execute a reduced critical-path-only test suite that completes in under 2 minutes.
