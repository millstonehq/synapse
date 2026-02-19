---
id: POLICY-010
type: policy
title: OAuth Token Lifecycle Policy
status: draft
owner: VP Engineering
created: '2024-09-02T06:52:37.971Z'
updated: '2026-08-08T15:58:26.858Z'
tags:
  - policy
  - user-authentication
summary: OAuth Token Lifecycle Policy
example: true
related_standards:
  - STANDARD-009
  - STANDARD-010
---

## Scope

This policy covers the complete lifecycle of OAuth 2.0 access tokens, refresh tokens, and authorization codes issued by any authorization server operated by the organization. It applies to all OAuth clients (first-party applications, partner integrations, and internal service-to-service flows) and all authorization servers managing these tokens.

## Rationale

- OAuth tokens represent delegated access; their misuse directly enables unauthorized resource access on behalf of users
- Access token lifetimes that are too long increase the window of token exposure after a breach or user revocation
- Refresh tokens require special handling due to their longer lifetime and ability to generate new access tokens
- Clear token revocation processes are required to enforce access removal when users are offboarded or integrations are terminated

## Policy Statements

- Access token lifetime must not exceed 15 minutes for user-facing flows and 1 hour for machine-to-machine flows
- Refresh tokens must expire after 30 days of inactivity or 90 days absolute, whichever comes first
- Authorization codes must expire within 60 seconds of issuance and may only be used once
- Refresh token rotation must be enforced: each use of a refresh token must invalidate it and issue a new one
- Revoked tokens must be honored within 5 minutes across all resource servers via token introspection or short-lived token strategy
- OAuth clients must use PKCE for all authorization code flows regardless of client type
- Token issuance, usage, and revocation events must be logged per [[STANDARD-009|Password Hashing Standard]] and audit requirements

## Related Standards

- [[STANDARD-009|Password Hashing Standard]]
- [[STANDARD-010|Session Cookie Standard]]
