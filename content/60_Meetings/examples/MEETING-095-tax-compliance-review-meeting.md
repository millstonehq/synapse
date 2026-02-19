---
id: MEETING-095
type: meeting
title: Tax Compliance Review Meeting
status: approved
owner: Principal Engineer
created: '2024-11-30T20:47:46.083Z'
updated: '2025-12-06T06:29:44.427Z'
tags:
  - meeting
  - billing-engine
summary: Tax Compliance Review Meeting
company: BillingEngine
topic: Tax Compliance Review Meeting
meeting_date: '2024-01-25T07:16:50.718Z'
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
- **Topic**: Tax Compliance Review Meeting
- **Date/Time**: 2024-01-25 07:16 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Annual tax compliance review ahead of Q1 tax filing season. Finance team requested an engineering review of the tax calculation logic, jurisdiction coverage, and compliance gaps relative to current nexus obligations. Several US states have added economic nexus thresholds that may now apply.

## Observations by Domain

- **US Sales Tax**: The platform currently tracks nexus in 8 states; post-Wayfair analysis by Finance indicates we now have economic nexus in 14 states — 6 states need to be added to the tax calculation jurisdiction table
- **EU VAT**: EU VAT rates are current; reverse-charge logic for B2B transactions is correctly implemented. Gap: digital services VAT for B2C transactions to EU countries was not being applied to annual subscription invoices (only monthly)
- **Tax Exemption Handling**: Tax exemption flags are applied correctly; however, exemption certificates are not stored in the billing system — Finance is managing them in a separate spreadsheet
- **Audit Trail**: Tax calculation logs include rate and jurisdiction but do not include the jurisdiction determination logic (why a customer was assigned a given jurisdiction)

## Key Metrics & Data Points

- **US states with active nexus**: 8 (should be 14 per Finance analysis)
- **EU B2C VAT gap**: Annual subscriptions not applying digital services VAT — estimated exposure: $18,000/year
- **Tax exemption accounts**: 23 exempt accounts (managed outside billing system)
- **Tax calculation log completeness**: Jurisdiction assignment reason not logged (audit gap)

## Preliminary Scorecard Hooks

- US Tax Nexus Coverage: 2/5 - 6 states missing; material compliance gap
- EU VAT Compliance: 3/5 - B2B correct; B2C annual subscription gap identified
- Tax Exemption Management: 2/5 - No platform support for certificate storage; manual process
- Audit Trail Quality: 3/5 - Rate and amount logged; jurisdiction determination reasoning missing

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Missing nexus in 6 US states | High | Certain | Principal Engineer | Add 6 jurisdictions to tax rate table and enable nexus tracking | 2024-02-15 |
| EU B2C VAT gap on annual subscriptions | High | Certain | Tech Lead | Fix VAT application logic to apply to all billing periods, not just monthly | 2024-02-01 |
| Tax exemption certificates not in system | Medium | Certain | Engineering Manager | Build exemption certificate storage in billing admin console | 2024-03-31 |

## Decisions & Next Steps

### Decisions

- EU B2C VAT fix is P0 — must be deployed before February billing cycle
- US nexus expansion will be completed in two phases: 4 states by Feb 15, remaining 2 by March 1
- Tax exemption certificate storage will be scoped and prioritized for Q1

### Action Items

- Tech Lead: Fix EU B2C VAT on annual subscriptions by 2024-01-31 (before February cycle)
- Principal Engineer: Add 4 priority US nexus jurisdictions to tax rate table by 2024-02-10
- Engineering Manager: Create PRD for tax exemption certificate storage feature

### Follow-ups

- Finance to provide the 6 new US jurisdiction codes and applicable rates
- Follow-up review after February billing cycle to confirm VAT fix is applied correctly
