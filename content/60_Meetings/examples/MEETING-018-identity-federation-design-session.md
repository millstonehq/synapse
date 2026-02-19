---
id: MEETING-018
type: meeting
title: Identity Federation Design Session
status: approved
owner: Principal Engineer
created: '2024-10-29T04:18:16.902Z'
updated: '2025-03-05T11:00:50.429Z'
tags:
  - meeting
  - user-authentication
summary: Identity Federation Design Session
company: UserAuthentication
topic: Identity Federation Design Session
meeting_date: '2025-05-24T12:17:28.879Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Enterprise Identity Federation
- **Topic**: Identity Federation Design Session — Cross-Tenant SAML Federation Architecture
- **Date/Time**: 2025-05-24 10:30 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Design session to architect cross-tenant identity federation to support enterprise customers who need their employees to access our platform using their own corporate identity providers without creating separate platform accounts.

## Observations by Domain

- **Federation Model**: SAML 2.0 SP-initiated SSO is the right choice for enterprise compatibility; most corporate IdPs (Azure AD, Okta, ADFS) support it natively
- **Tenant Isolation**: Federation must be strictly scoped per tenant; a user authenticating via Tenant A's IdP must not gain access to Tenant B's resources
- **Attribute Mapping**: Corporate IdPs vary in their claim schemas; a flexible attribute mapping configuration per federation trust is required
- **Just-in-Time Provisioning**: JIT provisioning is the preferred model — user accounts are created in our system at first SAML login; no manual pre-provisioning required
- **SCIM Consideration**: Several enterprise prospects have asked about SCIM for automated user lifecycle management; this is out of scope for the initial federation release but should be in the roadmap

## Key Metrics & Data Points

- **Enterprise prospects requiring SAML federation**: 8 (representing ~$2.4M ARR opportunity)
- **Corporate IdP types in prospect pipeline**: Azure AD (5), Okta (2), ADFS (1)
- **Estimated implementation effort**: 6–8 weeks for core federation + JIT provisioning
- **SCIM roadmap estimate**: 4 additional weeks post-federation release

## Preliminary Scorecard Hooks

- Architecture Clarity: 4/5 - SAML 2.0 SP-initiated model is well-understood; design is solid
- Tenant Isolation: 4/5 - Isolation model is clear; will need careful implementation testing
- Enterprise Compatibility: 5/5 - SAML 2.0 is universally supported by enterprise IdPs in the pipeline
- Implementation Readiness: 3/5 - Core design agreed; attribute mapping flexibility and metadata management still to be detailed

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Tenant isolation misconfiguration allows cross-tenant access | High | Low | Principal Engineer | Mandatory security review and penetration test of federation tenant isolation before first customer onboarding | 2025-07-01 |
| SAML metadata expiry breaks federation without notice | High | Medium | Tech Lead | Implement metadata expiry monitoring and automated renewal alerts | 2025-06-15 |
| Attribute mapping inflexibility blocks enterprise onboarding | Medium | Medium | Tech Lead | Design attribute mapping as a per-tenant configuration; test with all 3 IdP types in staging | 2025-06-30 |

## Decisions & Next Steps

### Decisions

- SAML 2.0 SP-initiated federation with JIT provisioning is the approved architecture for V1
- SCIM support is added to the product roadmap as a Q4 initiative
- A security review and penetration test of tenant isolation must be completed before first enterprise customer is onboarded

### Action Items

- Write technical design document for federation and JIT provisioning (Principal Engineer — 2025-06-07)
- Build SAML metadata management and expiry monitoring (Tech Lead — 2025-06-15)
- Design per-tenant attribute mapping configuration schema (Tech Lead — 2025-06-15)
- Schedule security review for tenant isolation testing (Engineering Manager — 2025-06-30)

### Follow-ups

- Federation implementation kickoff sprint begins 2025-06-03
- First enterprise customer beta onboarding target: 2025-07-15
