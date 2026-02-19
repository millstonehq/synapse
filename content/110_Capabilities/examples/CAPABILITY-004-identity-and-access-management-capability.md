---
id: CAPABILITY-004
type: capability
title: Identity and Access Management Capability
status: approved
owner: VP Engineering
created: '2024-10-26T15:42:32.195Z'
updated: '2026-10-27T23:19:43.143Z'
tags:
  - capability
  - user-authentication
summary: Identity and Access Management Capability
evidence_links:
  - POLICY-007
  - PROCESS-007
  - PROCESS-012
example: true
---

## Domain

- Identity provisioning and deprovisioning for users and service accounts
- Authentication protocol support (local credentials, SSO via SAML/OIDC, passwordless, social login)
- Authorization model (RBAC, permission propagation via JWT claims)
- Session lifecycle management (creation, timeout enforcement, concurrent session limits)
- Audit trail for authentication and authorization events

## Maturity (0-5)

- Authentication protocols: 4/5 - Supports password, TOTP MFA, WebAuthn, SAML 2.0, OIDC, and magic links; passkey adoption growing; social login in late stages
- Authorization model: 3/5 - RBAC with permission embedding in JWT is implemented; fine-grained attribute-based access control (ABAC) is not yet available
- Session management: 4/5 - Redis-backed sessions with sliding and absolute timeouts, concurrent session limits; adaptive session policies not yet implemented
- Identity provisioning: 3/5 - JIT provisioning via SSO is available; SCIM automated provisioning is not yet implemented; manual invitation flow is the primary onboarding path
- Audit and compliance: 3/5 - Authentication events logged and queryable; admin actions logged; log retention meets 90-day requirement; log-based alerting for suspicious patterns is limited

## Metrics

- Monthly Active Users with MFA enrolled: currently 79.4% (target: 90%)
- SSO adoption among enterprise organizations: 64% (target: 75%)
- Authentication service availability: 99.97% (target: 99.95%)
- Mean time to provision a new user: < 60 seconds via JIT SSO; ~2 hours via invitation flow
- Audit log query response time: P99 < 2 seconds for 30-day date range queries

## Evidence Links

- [[POLICY-007|User Authentication Policy]] — Governing policy for authentication requirements
- [[PROCESS-007|User Onboarding Process]] — Process for provisioning new users
- [[PROCESS-012|Access Review Process]] — Quarterly access review process for privilege validation

## Notes

- SCIM automated provisioning is on the 12-month roadmap; current manual deprovisioning is a compliance gap for SOC 2 control CC6.2
- Adaptive MFA (risk-based challenge decisions) is in PRD stage; will improve the maturity of the Authentication protocols area to 5/5 when shipped
