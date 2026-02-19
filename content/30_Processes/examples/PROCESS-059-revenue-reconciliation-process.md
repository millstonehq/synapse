---
id: PROCESS-059
type: process
title: Revenue Reconciliation Process
status: approved
owner: Director of Engineering
created: '2024-01-25T05:54:15.513Z'
updated: '2026-05-29T12:50:33.405Z'
tags:
  - process
  - billing-engine
summary: Revenue Reconciliation Process
related_standards:
  - STANDARD-059
  - STANDARD-060
related_sops:
  - SOP-096
  - SOP-094
related_systems:
  - SYSTEM-049
example: true
---

## Purpose

The Revenue Reconciliation Process verifies that billed amounts, collected payments, and recognized revenue entries are consistent across the Billing Engine, the payment gateway, and the financial ledger. It is executed after each monthly billing cycle to detect and resolve any discrepancies before financial reports are closed.

Accurate reconciliation is essential for financial statement integrity and ensures that the engineering platform's billing outputs align with Finance's reporting.

## Scope

- Reconciliation of total billed amounts against payment gateway settlement records
- Reconciliation of finalized invoices against revenue recognition events in the financial ledger
- Detection and investigation of orphaned billing records, missed payments, and duplicate charges
- Currency conversion reconciliation for multi-currency accounts

## Roles and Responsibilities

- **Billing Platform Engineer**: Runs the reconciliation job, reviews discrepancy reports, and investigates flagged items
- **Finance Operations**: Reviews the reconciliation summary report, confirms ledger entries, and signs off on period close
- **Director of Engineering**: Resolves escalated discrepancies that cannot be explained by known platform behavior
- **External Auditors**: Access reconciliation records during SOC 2 and financial audits

## Triggers

- Monthly trigger: automatically runs 48 hours after the billing cycle payment collection step completes
- Manual trigger by Finance Operations at quarter end for additional verification before earnings reporting

## Inputs

- Finalized invoice records for the billing period from the billing database
- Payment settlement records from the payment gateway for the same period
- Revenue recognition event log from the billing event bus
- Currency exchange rates used during the period

## Outputs

- Reconciliation report showing matched and unmatched records across billing, payments, and ledger
- Discrepancy tickets for any unmatched records exceeding the materiality threshold ($50 per record)
- Signed period-close confirmation from Finance Operations
- Reconciliation archive record stored per the Invoice Retention Policy

## Steps

1. Reconciliation job fetches all finalized invoice records for the closed billing period
2. Job fetches corresponding payment settlement records from the payment gateway API for the same period
3. Job fetches revenue recognition events from the billing event bus log for the period
4. Three-way match is performed: each invoice is matched to a payment record and a revenue recognition event
5. Unmatched records are written to the discrepancy report with category: `missing_payment`, `missing_revenue_event`, or `amount_mismatch`
6. Billing Platform Engineer reviews the discrepancy report and investigates each flagged item, resolving or escalating as appropriate
7. Finance Operations reviews the reconciliation summary and approves period close once all material discrepancies are resolved
8. Reconciliation report is archived with a timestamp and Finance sign-off attached

## Controls

- Reconciliation must complete within 5 business days of billing cycle completion to meet finance reporting deadlines
- Discrepancies exceeding $1,000 in aggregate must be escalated to the Director of Engineering before period close
- Reconciliation job runs must be idempotent; re-runs must not create duplicate discrepancy tickets
