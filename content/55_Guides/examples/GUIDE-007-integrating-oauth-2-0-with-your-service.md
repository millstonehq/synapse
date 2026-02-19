---
id: GUIDE-007
type: guide
title: Integrating OAuth 2.0 with Your Service
status: approved
owner: Engineering Team
created: '2025-03-08T07:55:14.656Z'
updated: '2025-07-24T10:15:33.645Z'
tags:
  - guide
  - user-authentication
summary: Integrating OAuth 2.0 with Your Service
audience: partner
related_systems:
  - SYSTEM-007
  - SYSTEM-009
related_sops:
  - SOP-014
  - SOP-012
example: true
---

## Why OAuth 2.0

OAuth 2.0 enables your service to verify user identity and access rights without handling passwords directly. Instead of asking users for credentials, your service redirects them to our authorization server, which handles authentication and returns a JWT access token your service can use to make authorized API calls.

This separation of concerns means your service never sees passwords, your users authenticate against a single trusted authority, and access can be revoked centrally without touching your service. For partner integrations, OAuth 2.0 with PKCE is the required flow.

## Prerequisites

Before you begin, you need a registered OAuth client. Submit a request via the OAuth Client Registry with your application name, intended redirect URIs, and the scopes you need. You will receive a `client_id` and, if your client is a confidential server-side application, a `client_secret` to store securely.

Review the OAuth Scope Naming Standard to understand which scopes to request. Request only the minimum scopes needed for your use case.

## Implementing the Authorization Code Flow with PKCE

The authorization code flow with PKCE is required for all partner and public clients. Here is the flow:

1. Generate a random `code_verifier` (43–128 characters) and compute a `code_challenge` as `BASE64URL(SHA256(code_verifier))`.
2. Redirect the user to `https://auth.example.com/authorize?response_type=code&client_id=<your_client_id>&redirect_uri=<your_uri>&scope=<requested_scopes>&code_challenge=<challenge>&code_challenge_method=S256`.
3. After the user authenticates, the authorization server redirects back to your `redirect_uri` with a `code` parameter.
4. Exchange the code for tokens: `POST /token` with `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, and `code_verifier`.
5. The token endpoint returns an access token (JWT) and a refresh token. Store the refresh token securely; never expose it to the browser or client-side code.

## Validating Access Tokens

Your service must validate access tokens on every request. The access token is a JWT signed by our authorization server. Validate it by:

- Fetching our JWKS endpoint (`GET //.well-known/jwks.json`) and caching the response for the duration of the key's rotation cycle
- Verifying the token signature against the public key matching the token's `kid` header
- Verifying `iss` equals `https://auth.example.com`, `aud` includes your service's identifier, and `exp` is in the future

Do not validate tokens by calling our introspection endpoint on every request — that creates a synchronous dependency. Use local JWKS-based validation.

## Common Questions

If your refresh token request returns a 401, the token has been revoked or expired. Redirect the user through the authorization flow again. Refresh tokens rotate on each use; always store the newest refresh token returned by the token endpoint, discarding the previous one.
