---
id: MEETING-092
type: meeting
title: Revenue Recognition Workshop
status: deprecated
owner: Product Manager
created: '2024-01-02T05:29:39.129Z'
updated: '2026-04-09T14:43:25.326Z'
tags:
  - meeting
  - billing-engine
summary: Revenue Recognition Workshop
company: BillingEngine
topic: Revenue Recognition Workshop
meeting_date: '2024-10-01T05:08:54.690Z'
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
- **Topic**: Revenue Recognition Workshop
- **Date/Time**: 2024-10-01 05:08 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Cross-functional workshop to align engineering and finance on revenue recognition rules for the new multi-year contract billing model and ensure the Billing Engine emits events that meet ASC 606 reporting requirements.

## Observations by Domain

- **ASC 606 Compliance**: Current billing event schema does not distinguish between earned and deferred revenue — Finance is manually adjusting the ledger each month for prepaid annual contracts
- **Multi-Year Contracts**: The billing engine has no native support for multi-year contract schedules; Finance is managing these manually in spreadsheets
- **Usage Revenue**: Usage-based revenue is being recognized at invoice finalization rather than at the period it was earned (timing mismatch of up to 30 days)
- **Event Granularity**: Revenue recognition events lack the contract ID and performance obligation reference needed to satisfy audit requirements

## Key Metrics & Data Points

- **Annual contract accounts**: 47 accounts billed annually (manually managed by Finance)
- **Monthly Finance adjustment effort**: 8 hours per month reconciling deferred revenue
- **Timing mismatch for usage revenue**: Up to 30 days between usage occurrence and recognition
- **Audit gap**: 0 of 47 annual contracts have machine-readable performance obligation references

## Preliminary Scorecard Hooks

- Revenue Recognition Accuracy: 2/5 - Functional but manual adjustments required; timing mismatches present
- Event Schema for Finance: 2/5 - Missing contract ID, performance obligation reference, and earned/deferred distinction
- Multi-Year Contract Support: 1/5 - No native platform support; fully manual
- Audit Readiness: 3/5 - Data exists but is not structured for automated audit extraction

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| ASC 606 audit finding due to timing mismatch | High | Medium | Principal Engineer | Emit recognition events tied to usage period, not invoice date | 2024-11-30 |
| Manual spreadsheet errors in annual contract management | High | High | Engineering Manager | Build multi-year contract schedule support in billing engine | 2025-01-31 |
| Missing performance obligation references in events | Medium | High | Tech Lead | Add `contract_id` and `obligation_id` fields to recognition event schema | 2024-11-15 |

## Decisions & Next Steps

### Decisions

- Revenue recognition events must be emitted with the `occurred_at` of the usage period, not the invoice generation timestamp
- Multi-year contract schedules will be a Q1 2025 engineering initiative
- Event schema v3 will add `contract_id`, `obligation_id`, and `revenue_type` (earned/deferred) fields

### Action Items

- Tech Lead: Update recognition event emission to use usage period timestamps by 2024-11-30
- Principal Engineer: Design multi-year contract data model, share with Finance for review by 2024-11-15
- Engineering Manager: Prioritize event schema v3 fields in Q4 sprint backlog

### Follow-ups

- Finance to provide test cases for annual contract revenue schedule validation
- Follow-up workshop on multi-year contract design once PRD is drafted
