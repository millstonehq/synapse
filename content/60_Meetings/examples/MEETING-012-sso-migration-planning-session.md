---
id: MEETING-012
type: meeting
title: SSO Migration Planning Session
status: draft
owner: Engineering Manager
created: '2024-01-01T15:25:36.540Z'
updated: '2025-05-29T07:56:46.884Z'
tags:
  - meeting
  - user-authentication
summary: SSO Migration Planning Session
company: UserAuthentication
topic: SSO Migration Planning Session
meeting_date: '2025-04-14T14:46:57.002Z'
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

- **Project**: SSO Provider Migration
- **Topic**: SSO Migration Planning Session — Okta to In-House IdP
- **Date/Time**: 2025-04-14 2:00 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Planning session for migrating approximately 12,000 users from Okta to the in-house Identity Provider Service as part of a platform consolidation initiative.

## Observations by Domain

- **User Impact**: Migration will force users to re-authenticate once; JIT provisioning will create accounts in the new IdP at first login to minimize manual migration work
- **Protocol Compatibility**: In-house IdP supports OIDC 1.0 and SAML 2.0; all existing integrations that support standard protocols will work without code changes
- **Attribute Mapping**: Okta custom attributes (`department`, `costCenter`) are not standard OIDC claims; mapping strategy needs to be defined before migration
- **Enterprise Customers**: 14 enterprise customers use Okta SAML federation; each requires a new SAML metadata exchange with the in-house IdP
- **Timeline Risk**: Enterprise customer coordination adds 4–6 weeks to the migration timeline due to change approval processes on their side

## Key Metrics & Data Points

- **Total users to migrate**: 12,400 across 3 tenants
- **Enterprise SAML integrations**: 14 (requiring individual customer coordination)
- **Estimated migration window per cohort**: 4 days per 20% cohort
- **Estimated full migration timeline**: 8–10 weeks including enterprise customer transitions
- **Current Okta contract expiry**: 12 weeks from meeting date

## Preliminary Scorecard Hooks

- Migration Readiness: 2/5 - Attribute mapping not resolved; dual-provider mode not yet implemented
- Enterprise Coordination: 1/5 - No customer outreach has begun; 14 customers need individual coordination
- Technical Feasibility: 4/5 - Protocol compatibility confirmed; JIT provisioning design complete
- Timeline Risk: 3/5 - Feasible within contract window but leaves minimal buffer

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Attribute mapping gaps break downstream RBAC | High | High | Principal Engineer | Complete attribute mapping design before any migration begins | 2025-04-28 |
| Enterprise customer coordination delays exceed contract window | High | Medium | Engineering Manager | Begin customer outreach immediately; escalate if delays emerge | 2025-04-21 |
| Dual-provider mode not ready in time | High | Low | Tech Lead | Dual-provider implementation is sprint 1 priority | 2025-04-28 |
| User confusion from forced re-authentication | Low | High | Product Manager | Draft and send user communication 2 weeks before migration start | 2025-05-05 |

## Decisions & Next Steps

### Decisions

- Dual-provider mode must be fully implemented and tested before the first user cohort is migrated
- Attribute mapping design is a blocking dependency; must be completed before implementation begins
- Enterprise customers will be migrated in a separate wave after the standard user migration is complete

### Action Items

- Complete attribute mapping design document (Principal Engineer — 2025-04-28)
- Implement dual-provider mode in auth service (Tech Lead — 2025-04-28)
- Draft enterprise customer communication and migration coordination guide (Engineering Manager — 2025-04-21)
- Define migration cohort schedule and rollback criteria (Platform Lead — 2025-05-05)

### Follow-ups

- Weekly migration status sync starting 2025-04-21
- Gate review before first cohort migration to confirm all blockers resolved
