---
id: PROCESS-070
type: process
title: Billing Audit Preparation Process
status: approved
owner: Platform Lead
created: '2025-02-08T20:48:57.084Z'
updated: '2025-11-17T18:27:40.054Z'
tags:
  - process
  - billing-engine
summary: Billing Audit Preparation Process
related_standards:
  - STANDARD-058
  - STANDARD-056
related_sops:
  - SOP-100
  - SOP-099
related_systems:
  - SYSTEM-047
example: true
---

## Purpose

This process defines the steps required to prepare the Billing Engine's financial records, system configurations, and supporting documentation for an external financial audit. An annual audit is required at our revenue scale to satisfy investor agreements and to maintain customer trust for enterprise deals that require SOC 2 or similar assurance. Preparation must begin 8 weeks before the scheduled audit start date to allow sufficient time for evidence collection, gap remediation, and Finance review. This process references [[STANDARD-058|STANDARD-058]] (invoice content controls) and [[STANDARD-056|STANDARD-056]] (subscription state controls), and relies on the [[SYSTEM-047|Usage Metering Service]] as a primary evidence source for usage-based revenue claims.

## Scope

- Financial ledger completeness and accuracy (double-entry ledger for the audit period)
- Invoice accuracy and completeness for a sample of invoices selected by the auditor
- Tax calculation and filing records for all active jurisdictions
- Access control evidence for the Billing Engine and its supporting systems
- Subscription state change audit trail for the audit period

## Roles and Responsibilities

- **Controller (Finance)**: Owns the audit relationship; coordinates with external auditor; approves all evidence packages before submission
- **Billing Tech Lead (Engineering)**: Responsible for generating technical evidence exports; remediating any system-level audit findings; attending technical review sessions with auditors
- **Revenue Operations Manager (Finance)**: Produces trial balance reports, reconciliation evidence, and revenue recognition schedules from the internal ledger
- **Security Lead**: Provides access control evidence (user provisioning records, SSO logs, privilege reviews)
- **Billing On-Call**: Available during audit evidence collection period to answer auditor questions about system behavior

## Triggers

- Annual audit preparation begins 8 weeks before the scheduled audit date (Controller sets the date by January 15 each year)
- Mid-year unscheduled audit triggered by investor request or regulatory inquiry
- Material billing system changes that require scope update to the existing audit opinion

## Inputs

- Audit scope document from external auditor (provided at audit kickoff)
- Prior year audit findings and management responses
- Billing Engine system documentation (system docs, ADRs, TDDs)
- Internal ledger data export for the audit period
- Avalara tax filing records for the audit period

## Outputs

- Evidence package for the auditor: invoice samples, ledger trial balance, tax records, access control logs
- Remediation plan for any control gaps identified during preparation
- Management representation letter (signed by Controller and VP Engineering)
- Audit completion sign-off from external auditor

## Steps

1. **Controller** confirms audit dates and scope with the external auditor; communicates start date and scope to Billing Tech Lead and Revenue Operations Manager
2. **Revenue Operations Manager** generates a trial balance from the double-entry ledger for the audit period; reconciles against Stripe payment records and identifies any variances above the materiality threshold ($500)
3. **Billing Tech Lead** exports the subscription state event audit log for the audit period from [[SYSTEM-047|Usage Metering Service]] and the Subscription Management Service; validates completeness (no gaps in the sequence)
4. **Revenue Operations Manager** prepares the revenue recognition schedule (deferred revenue roll-forward, recognition by period) using the internal ledger
5. **Billing Tech Lead** documents any system changes made during the audit period that affected invoice generation, tax calculation, or revenue recognition; maps changes to their ADRs and TDDs
6. **Security Lead** compiles access control evidence: user provisioning records for the audit period, privilege review records, SSO access logs for the billing production environment
7. **Controller** reviews all evidence packages for completeness and accuracy; submits to the external auditor per the agreed evidence submission schedule (SOP-100, SOP-099)
8. **Billing Tech Lead** is available for auditor Q&A sessions during the audit fieldwork period (typically 2-3 days)

## Controls

- Audit evidence packages must be reviewed and approved by the Controller before submission to the external auditor
- Access control evidence must cover the full audit period with no gaps; any gaps must be documented and explained
- Variance in the ledger reconciliation above the materiality threshold ($500) must be investigated and resolved or formally documented before evidence submission
- All evidence exports must be version-controlled and timestamped; ad-hoc queries used for evidence must be documented with their exact SQL
- Audit findings from prior years must be reviewed at process kickoff to ensure remediation was completed and is evidenced
