---
id: ADR-0006
type: adr
title: Adopt Auth0 as Identity Provider
status: approved
owner: Principal Engineer
created: '2025-01-14T08:23:02.127Z'
updated: '2026-05-26T16:37:29.705Z'
tags:
  - adr
  - user-authentication
summary: Adopt Auth0 as Identity Provider
example: true
---

## Context

The platform currently manages user authentication through a homegrown credential store and a custom session management system. As the product scales, the team is facing recurring pain points: implementing MFA securely, managing social login integrations, handling enterprise SSO (SAML/OIDC), and staying current with evolving authentication standards. Each of these features requires significant ongoing engineering investment to implement correctly and maintain securely.

We have approximately 150,000 users today and are forecasting 500,000 within 18 months. The current system was designed for a simpler single-product use case and does not support multi-tenancy, organization-level SSO configuration, or the range of MFA factors our enterprise customers require. Three enterprise prospects have specifically cited authentication limitations as blockers to signing contracts.

The team evaluated whether to build these capabilities in-house or adopt an identity provider (IdP) platform. The build-vs-buy analysis showed that replicating the security surface of a mature IdP would require 2-3 senior engineers for 12+ months and introduce significant security risk during the build period.

## Decision

We will adopt **Auth0 by Okta** as our identity provider. Auth0 will handle credential storage, MFA, social login, and enterprise SSO. Our Auth Service will be retained as a thin orchestration layer that delegates to Auth0 for identity operations and continues to issue platform-specific JWT claims and manage session state.

The migration will be phased: new users will be provisioned in Auth0 immediately; existing users will be migrated in batches over 90 days with an automated migration path that migrates credentials on next login (hash migration pattern).

## Consequences

**Positive:**
- Enterprise SSO (SAML/OIDC) available immediately via Auth0's built-in connections, unblocking three enterprise deals
- MFA (TOTP, SMS, WebAuthn) provided out-of-box with no implementation cost
- Auth0 maintains SOC 2 Type II and ISO 27001, simplifying our compliance posture
- Reduces ongoing security maintenance burden for authentication logic

**Negative:**
- SaaS dependency introduces a new availability risk; Auth0 outages directly impact our authentication
- Per-MAU pricing model will become significant cost at 500K+ users; need to track and forecast
- Customization is constrained to Auth0's action/rule framework; complex authorization logic must remain in-house
- Migration of 150,000 existing users carries execution risk; hash migration adds complexity

**Neutral:**
- Our Auth Service remains as a platform-specific layer, so downstream services do not need to change their token validation logic
- The Auth0 management API provides audit log access, maintaining our compliance evidence chain

## Alternatives Considered

**Build in-house (extend current system)**:
- Pro: Full control over implementation, no external dependency, no per-user cost
- Con: 12+ months of senior engineer time, high security risk during build, ongoing maintenance burden
- Rejected because: Time to market is too long given enterprise pipeline requirements, and in-house auth security is a difficult problem we have already underinvested in

**Keycloak (self-hosted open source)**:
- Pro: No per-user cost, full control, open source, strong enterprise SSO support
- Con: Significant operational overhead to run a highly available, secure Keycloak cluster; requires dedicated Keycloak expertise; no managed SLA
- Rejected because: Operational overhead offsets the cost savings at our scale, and we lack the internal Keycloak expertise to operate it safely
