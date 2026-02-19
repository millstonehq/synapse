---
id: MEETING-099
type: meeting
title: Subscription Model Strategy Session
status: accepted
owner: Engineering Manager
created: '2025-01-24T05:55:57.203Z'
updated: '2025-06-21T16:14:34.120Z'
tags:
  - meeting
  - billing-engine
summary: Subscription Model Strategy Session
company: BillingEngine
topic: Subscription Model Strategy Session
meeting_date: '2024-03-16T12:56:11.078Z'
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

- **Project**: Billing Engine Platform
- **Topic**: Subscription Model Strategy Session
- **Date/Time**: 2024-03-16 12:56 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Strategic session to evaluate the current subscription model architecture and determine what changes are needed to support the upcoming product pricing strategy: moving from a single-tier subscription to a multi-tiered model with optional add-ons and annual/monthly toggle.

## Observations by Domain

- **Current Model Limitations**: The current billing engine supports a single active plan per account; the new pricing strategy requires a base plan plus up to 4 add-ons simultaneously
- **Annual/Monthly Toggle**: Annual billing is not currently supported in the billing engine — all subscriptions bill monthly. Adding annual billing requires changes to the proration engine, the revenue recognition event schema, and the dunning workflow
- **Add-On Architecture**: Add-ons could be modeled as separate subscription objects or as plan modifiers on the base plan. The "separate subscription objects" approach is more flexible but adds complexity to invoice generation
- **Trial Period Strategy**: Product wants to support per-add-on trial periods (not just account-level trials). This is not currently supported in the subscription model

## Key Metrics & Data Points

- **Accounts that would benefit from add-on model**: Estimated 35% of Enterprise accounts based on CRM analysis
- **Annual billing revenue opportunity**: Projected $1.2M ARR uplift from annual commit discounts driving upgrades
- **Add-ons to support at launch**: 3 (Advanced Analytics, Priority Support, Custom Integrations)
- **Engineering estimate for annual billing**: 6-8 weeks (significant scope)

## Preliminary Scorecard Hooks

- Current Model Flexibility: 2/5 - Single plan per account is a hard constraint; add-ons require architectural changes
- Annual Billing Readiness: 1/5 - Not supported; requires 6-8 weeks of engineering work
- Add-On Architecture Options: 3/5 - Two viable approaches with clear trade-offs; decision needed
- Per-Add-On Trial Support: 2/5 - Not in scope for current sprint; needs dedicated sprint

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Multi-plan per account creates invoice generation complexity | High | Certain | Tech Lead | TDD required before implementation; invoice generation must aggregate all plan charges | 2024-04-01 |
| Annual billing delays Q2 pricing strategy launch | High | Medium | Engineering Manager | Scope annual billing as a separate workstream; monthly multi-plan launches first | 2024-03-31 |
| Per-add-on trials complicate subscription state machine | Medium | Medium | Principal Engineer | Defer per-add-on trials to v2; launch with account-level trial only | 2024-05-01 |

## Decisions & Next Steps

### Decisions

- Multi-plan per account (base + add-ons) will be implemented using separate subscription objects, not plan modifiers
- Annual billing will be a separate engineering workstream starting Q3; monthly billing launches with multi-plan support first
- Per-add-on trial periods are deferred to v2

### Action Items

- Tech Lead: Write TDD for multi-subscription per account invoice generation aggregation by 2024-04-01
- Principal Engineer: Design subscription state machine changes for multi-plan support by 2024-03-25
- Engineering Manager: Create Q3 workstream plan for annual billing implementation

### Follow-ups

- TDD review session: 2024-04-08
- Product manager to confirm Q2 launch scope given annual billing deferral
