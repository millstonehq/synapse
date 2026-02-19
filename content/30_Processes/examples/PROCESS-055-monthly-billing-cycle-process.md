---
id: PROCESS-055
type: process
title: Monthly Billing Cycle Process
status: approved
owner: Engineering Manager
created: '2025-10-16T18:38:18.135Z'
updated: '2026-05-12T06:25:39.455Z'
tags:
  - process
  - billing-engine
summary: Monthly Billing Cycle Process
related_standards:
  - STANDARD-059
  - STANDARD-056
related_sops:
  - SOP-092
  - SOP-091
related_systems:
  - SYSTEM-046
example: true
---

## Purpose

The Monthly Billing Cycle Process defines the end-to-end sequence for closing a billing period, generating invoices, collecting payments, and reconciling revenue for all active accounts. It ensures that billing runs are executed consistently, that all accounts are billed accurately, and that any failures are detected and resolved before invoices are delivered to customers.

This process runs on a fixed monthly schedule and must complete within the defined SLA window to meet contractual delivery dates and support downstream finance reporting.

## Scope

- All active subscription and usage-based billing accounts in the production Billing Engine
- Invoice generation, payment collection, and dunning workflows
- Revenue recognition event emission to the financial ledger
- Billing cycle exception handling (failed invoices, payment failures, credit applications)

## Roles and Responsibilities

- **Billing Platform Engineer**: Monitors the billing run job queue, resolves failed invoice generation tasks, and confirms cycle completion
- **Finance Operations**: Reviews the billing run summary report and approves revenue recognition entries before ledger posting
- **On-Call Engineer**: Responds to billing cycle alerts and escalates infrastructure issues that block cycle completion
- **Engineering Manager**: Approves any mid-cycle corrections or emergency adjustments to billing records

## Triggers

- Monthly scheduled trigger: first business day of the month at 02:00 UTC
- Manual trigger by Engineering Manager for off-cycle billing runs (e.g., contract terminations, retroactive adjustments)

## Inputs

- Finalized usage event aggregates for the closed billing period
- Active subscription and pricing plan configurations for all accounts
- Approved tax rate table for applicable jurisdictions
- Previous cycle carry-forward credits and adjustments

## Outputs

- Generated and finalized invoice records for all billable accounts
- Payment collection requests submitted to the payment gateway
- Revenue recognition events published to the financial ledger
- Billing cycle summary report with success/failure counts and total billed amount

## Steps

1. Billing scheduler triggers the cycle job and creates a billing run record with status `IN_PROGRESS`
2. Usage aggregation service computes per-account usage totals for the closed period from immutable event records
3. Billing engine generates draft invoices for all active accounts, applying pricing plans, discounts, and pending credits
4. Tax calculation service appends tax line items to each draft invoice based on the customer's billing jurisdiction
5. Invoice validation job checks each draft for schema compliance, zero-amount anomalies, and duplicate detection; failed drafts are routed to the exception queue
6. Billing Platform Engineer reviews the exception queue and resolves or escalates failed drafts before cycle finalization
7. Billing engine finalizes all validated invoices, assigns sequential invoice IDs, and publishes `billing.invoice.finalized` events
8. Payment collection job submits payment requests for all invoices to the configured payment gateway; failures initiate the dunning workflow

## Controls

- The billing cycle job must not finalize invoices for accounts flagged with a `billing_hold` status
- Failed invoice generation affecting more than 0.5% of the account population must halt the cycle and trigger an on-call page
- All billing run records are retained as audit trail entries and must not be deleted
- Finance Operations must sign off on the billing cycle summary before the payment collection step executes for amounts exceeding $500,000 total
