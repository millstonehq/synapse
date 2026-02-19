---
id: MEETING-090
type: meeting
title: Customer Self-Service Feature Planning
status: draft
owner: Engineering Manager
created: '2025-10-29T19:45:46.676Z'
updated: '2025-07-09T17:41:47.710Z'
tags:
  - meeting
  - customer-portal
summary: Customer Self-Service Feature Planning
company: CustomerPortal
topic: Customer Self-Service Feature Planning
meeting_date: '2026-03-29T15:42:05.133Z'
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

- **Project**: Customer Portal Platform
- **Topic**: Self-Service Feature Planning - Q2 2026 Roadmap Scope
- **Date/Time**: 2026-03-29 7:30 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Planning session to scope the Q2 self-service feature investment. Customer success team has escalated that 34% of support tickets are for tasks that should be self-serviceable in the portal. Goal is to reduce that percentage to below 15% by end of Q2.

## Observations by Domain

- **Support Ticket Analysis**: The top 5 "should be self-service" ticket categories are: user management (add/remove portal users), billing plan changes, API key rotation, data export, and invoice history download
- **Current Self-Service Coverage**: User management requires a support ticket; billing plan changes require a call with customer success; API key rotation exists in the portal but is hard to find; data export is available but limited; invoice history is downloadable
- **Engineering Complexity**: User management is the most complex (requires SSO provider integration); billing plan changes require payment provider API work; API key rotation and data export improvements are low complexity
- **Customer Readiness**: Recent customer survey shows 87% of customers prefer self-service for administrative tasks over waiting for support; 72% would use a guided wizard for plan changes if available
- **Risk Assessment**: User management and billing plan changes carry higher risk due to financial and access implications; they require audit logging and confirmation flows

## Key Metrics & Data Points

- **Support tickets solvable by self-service**: 34% of current volume
- **Customer self-service preference**: 87% prefer self-service for admin tasks
- **Top self-service request**: User management (42% of "should be self-service" tickets)
- **API key rotation discoverability**: Only 23% of customers know the feature exists
- **Target self-service ticket reduction**: From 34% to 15% by end of Q2

## Preliminary Scorecard Hooks

- Self-Service Coverage: 2/5 - Major gaps in user management and billing plan changes
- Feature Discoverability: 2/5 - Existing self-service features are hard to find (API key rotation)
- Engineering Feasibility: 4/5 - Most features are achievable in Q2 scope with appropriate resourcing
- Risk Management: 3/5 - Financial and access changes need careful audit and confirmation design
- Customer Readiness: 5/5 - Strong customer appetite for self-service; survey results are compelling

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Self-service billing changes create unintended downgrades | High | Medium | Product Manager | Require confirmation with plan summary and 24-hour cancellation window | 2026-04-05 |
| User management errors lock customers out of portal | High | Medium | Tech Lead | Prevent last-admin deletion; require email confirmation for new admin adds | 2026-04-05 |
| Scope too broad for Q2 delivery | Medium | High | Engineering Manager | Prioritize top 3 features only; API key + data export + user management | 2026-04-01 |

## Decisions & Next Steps

### Decisions

- Q2 self-service scope is prioritized to 3 features: user management, API key management improvements (discoverability + rotation), and data export enhancements
- Billing plan changes are deferred to Q3 due to payment provider integration complexity
- All new self-service features must include a comprehensive audit log viewable by portal admins

### Action Items

- Product Manager to write user management self-service spec (due 2026-04-08)
- Tech Lead to estimate user management feature effort for sprint planning (due 2026-04-05)
- Engineering Manager to update Q2 roadmap with approved scope and share with stakeholders (due 2026-04-01)

### Follow-ups

- Q2 self-service feature kick-off scheduled for first sprint of Q2 (2026-04-06)
- Support ticket volume to be measured monthly against the 15% target throughout Q2
