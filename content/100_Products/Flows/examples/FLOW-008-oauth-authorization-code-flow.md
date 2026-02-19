---
id: FLOW-008
type: flow
title: OAuth Authorization Code Flow
status: review
owner: QA Lead
created: '2025-03-19T04:01:51.953Z'
updated: '2026-06-05T14:17:30.126Z'
tags:
  - flow
  - user-authentication
summary: OAuth Authorization Code Flow
feature_area: User Authentication
related_prds:
  - PRD-008
example: true
---

## Steps

### Step 1: Authorization Request

The client application redirects the user to the authorization endpoint (`GET /authorize`) with the required OAuth 2.1 parameters: `response_type=code`, `client_id`, `redirect_uri`, `scope`, `state` (CSRF protection), `code_challenge`, and `code_challenge_method=S256` (PKCE). The authorization server validates that the `client_id` exists, the `redirect_uri` is in the client's registered allowlist, and the requested `scope` is permitted for the client.

### Step 2: User Authentication and Consent

The authorization server redirects the user to the platform login page if they are not already authenticated, or checks for an existing valid session. After authentication, if the client is a third-party application (not a first-party platform client), the user is shown a consent screen listing the requested scopes. For first-party clients, consent is implicit and the consent screen is skipped. The user confirms the consent grant.

### Step 3: Authorization Code Issuance

The authorization server generates a short-lived (60-second) authorization code, stores it in Redis along with the `code_challenge`, `client_id`, and `redirect_uri`, and redirects the user back to the client's `redirect_uri` with the `code` and `state` parameters. The client must verify the `state` matches the value it sent in Step 1.

### Step 4: Token Exchange

The client sends a `POST /token` request with `grant_type=authorization_code`, the received `code`, `redirect_uri`, `client_id`, and the `code_verifier` (the PKCE value that hashes to the previously provided `code_challenge`). The authorization server: validates the `code_verifier` against the stored `code_challenge` using SHA-256, verifies the `code` has not been used before (single-use), confirms the `redirect_uri` matches the stored value, and issues an access token (15-minute JWT) and refresh token (30-day opaque).

### Step 5: Token Usage and Refresh

The client uses the access token as a Bearer token in API request Authorization headers. Resource servers validate the JWT locally using the JWKS endpoint. When the access token expires (15 minutes), the client uses the refresh token to obtain a new access token via `POST /token` with `grant_type=refresh_token`. The refresh token is rotated on each use (single-use).

## Expected Results

- Client receives a valid access token and refresh token after completing the flow
- Access token is a signed JWT with correct `sub`, `aud`, `scope`, and expiry claims
- Authorization code is single-use and expires after 60 seconds
- PKCE code verifier is correctly validated on token exchange
- Refresh token rotation is enforced: old refresh token is invalidated on use

## User Info

| Field | Value |
|-------|-------|
| Role | Developer integrating an OAuth client application |
| Permissions | Client must be registered with the authorization server |
| Test account | test-oauth-client (client_id: test-client-001, redirect_uri: https://localhost:3000/callback) |
| Environment | Staging authorization server at https://auth.staging.example.com |
| Prerequisites | Client must have a registered client_id and pre-configured redirect URI allowlist |
