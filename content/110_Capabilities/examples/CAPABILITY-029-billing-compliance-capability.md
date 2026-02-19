---
id: CAPABILITY-029
type: capability
title: Billing Compliance Capability
status: approved
owner: Head of Engineering
created: '2025-06-26T19:24:17.278Z'
updated: '2026-10-31T23:39:08.396Z'
tags:
  - capability
  - billing-engine
summary: Billing Compliance Capability
evidence_links:
  - STANDARD-055
  - PROCESS-059
  - PROCESS-060
example: true
---

## Domain

- Tax Compliance (US and International)
- Financial Audit Readiness
- PCI DSS Compliance for Payment Processing

## Maturity (0-5)

- US sales tax compliance: 4/5 - Avalara AvaTax integrated; 42 US state nexus registrations current; rate update process automated
- International VAT/GST compliance: 3/5 - Avalara covers 28 countries; Finance-managed filing cadence established; EU OSS registration pending
- PCI DSS compliance: 4/5 - Annual self-assessment questionnaire (SAQ A) completed; no cardholder data stored internally; Stripe handles all card data
- Audit readiness: 3/5 - Double-entry ledger operational; audit trail complete; GAAP trial balance not yet automated
- Tax filing and remittance: 2/5 - Finance team uses Avalara portal manually; no automated filing integration

## Metrics

- Jurisdictions with automated tax calculation: 70 (42 US states + 28 countries)
- Tax calculation accuracy rate: 99.7% (measured by Finance monthly audit)
- Time to close books each month (Finance): 8 days (target: < 5 days)
- Outstanding nexus registrations past threshold: 0 (monitored monthly)
- PCI DSS SAQ A completion: Annual, last completed Q4 2024

## Evidence Links

- [[STANDARD-055|Tax Calculation Standard]] - Controls for tax rate accuracy and jurisdiction coverage
- [[PROCESS-059|Tax Filing Process]] - Monthly tax filing and remittance workflow
- [[PROCESS-060|Audit Preparation Process]] - Annual external audit preparation steps

## Notes

- Tax compliance maturity improved significantly following the Avalara integration (Q3 2024); the prior manual rate table approach resulted in two calculation errors
- Remaining gaps: EU OSS (One Stop Shop) VAT registration for EU digital services is pending Finance legal review; automated filing integration (connecting Avalara to remittance) is the next compliance initiative
- PCI DSS scope is narrow (SAQ A) because Stripe handles all card collection and storage; maintaining this scope is a compliance priority and informs architecture decisions
