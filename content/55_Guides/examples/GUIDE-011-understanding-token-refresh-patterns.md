---
id: GUIDE-011
type: guide
title: Understanding Token Refresh Patterns
status: approved
owner: Developer Experience
created: '2025-09-17T12:45:24.850Z'
updated: '2026-11-10T18:59:34.101Z'
tags:
  - guide
  - user-authentication
summary: Understanding Token Refresh Patterns
audience: partner
related_systems:
  - SYSTEM-009
  - SYSTEM-010
related_sops:
  - SOP-018
  - SOP-016
example: true
---

## The Problem Token Refresh Solves

Access tokens are short-lived by design — our access tokens expire in 15 minutes. Short-lived tokens limit the damage if a token is intercepted; an attacker who captures an expired token gets nothing. But you cannot ask your users to log in every 15 minutes. Refresh tokens solve this: they are long-lived credentials stored securely server-side that your service uses to obtain a new access token without requiring user interaction.

## How Refresh Token Rotation Works

We use rotating refresh tokens, which means every time you use a refresh token, it is invalidated and a new one is issued in the response. This provides detection capability: if a previously used refresh token is presented again, it indicates token theft, and all tokens in that family are immediately revoked.

Implementing this correctly requires: always storing the newest refresh token from the response (overwriting the previous one), never reusing a refresh token once you have received a new one, and treating a 401 response on the refresh endpoint as a signal to redirect the user through full re-authentication.

## Proactive vs. Reactive Refresh

There are two refresh strategies:

**Reactive**: Only refresh when an access token request returns 401. Simple to implement but causes a small latency spike for the user on the request that hits the expired token.

**Proactive**: Refresh the access token before it expires by checking the `exp` claim and initiating refresh when it is within 2 minutes of expiry. Eliminates user-visible latency from expiry but requires a background timer or middleware interceptor.

For services with user-facing latency requirements, proactive refresh is preferred. For background jobs or APIs that only need tokens occasionally, reactive refresh is acceptable.

## Refresh Token Storage

Refresh tokens must be stored server-side for web applications — never in browser `localStorage` or regular cookies. Store them in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie or in a server-side session. Mobile applications should use the platform secure storage (iOS Keychain, Android Keystore).

If your service architecture makes server-side storage impractical, use a backend-for-frontend (BFF) pattern: your server holds the refresh token and issues short-lived, scope-limited session tokens to the frontend.

## Handling Refresh Failures

When a refresh token request returns 401, do not retry with the same token. The token has been revoked or used by an attacker. Clear all stored tokens (access token and refresh token), clear the user's session, and redirect to the login page. Silently retrying a 401 on refresh can mask token theft events.
