---
id: MEETING-096
type: meeting
title: Billing Migration Planning Session
status: approved
owner: Product Manager
created: '2024-06-27T15:47:30.499Z'
updated: '2025-05-14T11:28:34.191Z'
tags:
  - meeting
  - billing-engine
summary: Billing Migration Planning Session
company: BillingEngine
topic: Billing Migration Planning Session
meeting_date: '2025-07-22T22:21:04.553Z'
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
- **Topic**: Billing Migration Planning Session
- **Date/Time**: 2025-07-22 22:21 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Planning session for the migration from the legacy billing system (v1, Stripe-only) to the new Billing Engine (v2, multi-provider, multi-currency). Approximately 12,000 active accounts and 3 years of invoice history need to be migrated without interrupting billing cycles.

## Observations by Domain

- **Data Volume**: 12,200 active accounts, 2.1M historical invoices, and 340M usage events to migrate; full migration estimated at 18 hours with current tooling
- **Billing Cycle Risk**: Migration must not span a billing cycle boundary — the target window is the 10-day gap between cycle close and next cycle start
- **Stripe Configuration**: Each active account has 1-3 Stripe objects (customer, subscription, payment method) that must be re-linked in the new system during migration
- **Dual-Write Phase**: A 30-day parallel-run is recommended to validate new system billing matches legacy before full cutover
- **Rollback Complexity**: Rolling back after cutover would require re-migrating 30 days of incremental billing data; rollback is only viable in the first 48 hours

## Key Metrics & Data Points

- **Active accounts to migrate**: 12,200
- **Historical invoices to migrate**: 2.1M
- **Estimated migration window required**: 18 hours (must fit in 10-day inter-cycle gap)
- **Dual-write validation period**: 30 days
- **Rollback viable window**: 48 hours post-cutover

## Preliminary Scorecard Hooks

- Migration Readiness: 2/5 - Tooling exists but 18-hour window is tight; parallelization needed
- Risk Mitigation: 3/5 - Dual-write plan is sound; rollback window is narrow and must be clearly communicated
- Data Validation: 3/5 - Reconciliation scripts exist but have not been tested at full production data volume
- Stakeholder Alignment: 4/5 - Finance and Support teams are briefed; customer communication plan is drafted

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Migration exceeds 10-day window | High | Medium | Principal Engineer | Parallelize account migration to reduce to under 8 hours; test at full scale | 2025-08-15 |
| Dual-write discrepancy reveals calculation differences | High | Medium | Tech Lead | Run dual-write validation in staging for 2 billing cycles before prod cutover | 2025-08-01 |
| Rollback after 48-hour window is infeasible | High | Low | Engineering Manager | Communicate hard rollback cutoff to all stakeholders; plan must be signed off | 2025-07-31 |

## Decisions & Next Steps

### Decisions

- Migration will proceed with a 30-day dual-write validation phase starting August 1
- Parallelization of account migration is required; target: under 8 hours for full migration
- Rollback will be officially unsupported after 48 hours post-cutover; all stakeholders must sign off

### Action Items

- Principal Engineer: Implement parallel migration runner, test at full volume by 2025-08-15
- Tech Lead: Set up dual-write validation pipeline in staging by 2025-08-01
- Engineering Manager: Get stakeholder sign-off on rollback timeline constraint by 2025-07-31

### Follow-ups

- Pre-migration checklist review: 2025-09-01
- Go/no-go decision meeting: 2025-09-15
