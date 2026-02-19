---
id: MEETING-015
type: meeting
title: OAuth Scope Simplification Workshop
status: approved
owner: Product Manager
created: '2025-09-27T23:39:57.571Z'
updated: '2026-02-05T05:12:35.671Z'
tags:
  - meeting
  - user-authentication
summary: OAuth Scope Simplification Workshop
company: UserAuthentication
topic: OAuth Scope Simplification Workshop
meeting_date: '2024-01-07T00:26:13.308Z'
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

- **Project**: OAuth Scope Simplification
- **Topic**: OAuth Scope Simplification Workshop — Reducing 47 Scopes to a Coherent Model
- **Date/Time**: 2024-01-07 1:00 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: The OAuth scope registry has grown organically to 47 scopes, many with overlapping semantics. This workshop was called to design a simplified scope model and plan the migration for existing OAuth clients.

## Observations by Domain

- **Current Scope Inventory**: 47 registered scopes analyzed; 12 are duplicates or deprecated with no active clients; 8 use non-standard naming conventions (e.g., `canReadOrders` vs `orders:read`)
- **Partner Impact**: 6 partner OAuth clients use the legacy non-standard scope names; a migration period is required before deprecated names can be removed
- **Scope Granularity**: Several scopes are over-broad (e.g., `admin` grants access to 12 different resource types); these need to be split into resource-specific admin scopes
- **Documentation Gap**: Only 31 of 47 scopes have descriptions in the authorization server's discovery endpoint; undocumented scopes cannot be self-served by partners
- **Scope Naming Standard Compliance**: Proposed new model follows the `<resource>:<action>` naming convention; all new scopes will comply from day one

## Key Metrics & Data Points

- **Total current scopes**: 47
- **Active scopes with registered clients**: 35
- **Deprecated/duplicate scopes with no clients**: 12
- **Non-standard named scopes requiring renaming**: 8
- **Partner clients requiring migration**: 6
- **Proposed new scope count**: 24 (47% reduction)

## Preliminary Scorecard Hooks

- Scope Model Clarity: 2/5 - Current model is inconsistent and confusing for new integrators
- Partner Impact: 3/5 - Migration is manageable with a 90-day deprecation period
- Standard Compliance: 4/5 - New model fully compliant with scope naming standard; migration path clear
- Documentation Coverage: 2/5 - Nearly 1/3 of scopes undocumented; this must be resolved during simplification

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Partner clients break during scope migration | High | Medium | Tech Lead | Maintain deprecated scope aliases for 90 days; proactive partner notification | 2024-02-01 |
| Scope simplification expands permissions inadvertently | High | Low | Principal Engineer | Security review of all scope permission mappings before publishing new model | 2024-01-21 |
| Incomplete documentation at launch | Medium | Medium | Product Manager | All 24 new scopes must have descriptions before the new model is published | 2024-02-07 |

## Decisions & Next Steps

### Decisions

- New scope model with 24 scopes approved in principle; final list subject to security review
- Deprecated scope aliases will be maintained for 90 days from publication date
- All new scopes must have discovery endpoint descriptions before the new model goes live

### Action Items

- Finalize 24-scope model and perform security review (Principal Engineer — 2024-01-21)
- Write documentation for all 24 new scopes (Product Manager — 2024-02-07)
- Notify 6 partner clients of the scope migration timeline and new scope names (Tech Lead — 2024-02-01)
- Configure deprecated scope aliases in authorization server (Tech Lead — 2024-02-14)

### Follow-ups

- Partner migration check-in calls to be scheduled by Tech Lead for 2024-03-01
- Final scope cleanup (removing deprecated aliases) targeted for 2024-05-07 after 90-day window
