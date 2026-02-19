---
id: GUIDE-009
type: guide
title: Implementing Custom Authentication Providers
status: approved
owner: Developer Experience
created: '2024-09-16T15:17:34.990Z'
updated: '2026-06-21T07:13:08.250Z'
tags:
  - guide
  - user-authentication
summary: Implementing Custom Authentication Providers
audience: partner
related_systems:
  - SYSTEM-007
  - SYSTEM-006
related_sops:
  - SOP-011
  - SOP-020
example: true
---

## What Is a Custom Authentication Provider

Our authentication service supports pluggable provider modules for cases where the built-in SSO options (Google, Okta, Azure AD) do not cover your requirements. A custom authentication provider is a module that implements the provider interface and allows the auth service to delegate credential verification to your logic while issuing standard JWTs on successful authentication.

Custom providers are appropriate for: legacy enterprise directory integrations, hardware token systems, and specialized B2B partner identity federation scenarios.

## Provider Interface

A custom authentication provider must implement the following interface:

```typescript
interface AuthProvider {
  name: string;
  verify(credentials: Credentials): Promise<AuthResult>;
  getUser(externalId: string): Promise<UserProfile>;
}
```

The `verify` method receives the user's credentials and returns an `AuthResult` with `success`, `externalId`, and optionally `mfaRequired`. The `getUser` method is called after successful verification to fetch the user's profile for JWT claim population.

Your provider runs server-side in a sandboxed module context. It cannot make outbound network calls to unapproved hosts; submit a network allowlist request during the approval process.

## Registration and Approval

Custom providers must go through a security review before being enabled. Submit a PR to the `auth-service/providers/` directory with your provider module and a test suite covering at minimum: successful authentication, invalid credentials, and error handling for provider unavailability.

The Security Engineer will review the provider code for: input sanitization, credential handling practices, error message safety (no credential echoing), and dependency vulnerability status. Approval from both the Security Engineer and Platform Lead is required.

## Testing Your Provider

The auth service includes a provider test harness. Run it with your provider module before submitting for review:

```
npm run provider:test -- --provider ./providers/my-custom-provider.ts
```

This runs the standard provider test suite including: credential verification, user profile mapping, error conditions, and injection attempt scenarios. All tests must pass before submission.

## Security Requirements

- Never log credential values; log only the authentication outcome and a masked user identifier
- Return generic error messages to callers; detailed errors should be internal logs only
- Implement a timeout on external calls your provider makes; do not allow auth service requests to hang
- Test your provider against the authentication logging requirements to confirm events are emitted correctly
