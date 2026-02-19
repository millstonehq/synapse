---
id: PROCESS-057
type: process
title: Invoice Generation Process
status: approved
owner: Platform Lead
created: '2025-09-17T17:43:06.531Z'
updated: '2026-07-25T01:05:17.545Z'
tags:
  - process
  - billing-engine
summary: Invoice Generation Process
related_standards:
  - STANDARD-055
  - STANDARD-060
related_sops:
  - SOP-091
  - SOP-096
related_systems:
  - SYSTEM-047
example: true
---

## Purpose

The Invoice Generation Process defines the steps for producing accurate, compliant invoices from billing data for both scheduled (monthly cycle) and on-demand (contract termination, mid-cycle adjustment) scenarios. It ensures that every invoice is generated from validated source data, correctly formatted, and delivered to the customer through the appropriate channel.

Invoice generation is a critical path operation. Failures in this process directly affect customer billing and revenue recognition.

## Scope

- Scheduled invoice generation as part of the monthly billing cycle
- On-demand invoice generation for contract changes, credits, and pro-ration scenarios
- Invoice PDF rendering and delivery to customers
- Invoice record persistence and event publication

## Roles and Responsibilities

- **Billing Engine Service**: Automated execution of invoice generation; the primary actor for scheduled runs
- **Platform Lead**: Oversees invoice generation health, resolves systematic failures, and approves any manual invoice overrides
- **Billing Platform Engineer**: Investigates individual failed invoices, performs root cause analysis, and reprocesses when appropriate
- **Customer Support**: Escalates invoice delivery failures reported by customers to the Billing Platform Engineer

## Triggers

- Monthly billing cycle scheduler reaches the invoice generation step
- Manual trigger from an authorized engineer for on-demand invoice generation
- Contract termination event requiring a final pro-rated invoice

## Inputs

- Finalized usage aggregates and subscription billing data for the account and period
- Applicable pricing plan configuration (rates, discounts, credits)
- Customer billing address and tax jurisdiction data
- Current tax rate table from the tax calculation service

## Outputs

- Finalized invoice record stored in the billing database with status `FINALIZED`
- Invoice PDF rendered and stored in document storage
- `billing.invoice.finalized` event published to the billing event bus
- Invoice delivery email or webhook notification dispatched to the customer

## Steps

1. Billing engine retrieves the account's billing data (usage aggregates, plan configuration, pending credits) for the invoice period
2. Line items are computed: subscription fees are rated against the plan, usage charges are calculated from aggregated events
3. Tax calculation service is called with the invoice amount and customer jurisdiction; tax line items are appended
4. Invoice total is calculated in the account's billing currency using integer arithmetic per the Currency Handling Standard
5. Invoice record is validated against the Invoice Format Standard schema; validation failures are written to the error log and the invoice is not finalized
6. Invoice PDF is rendered using the approved template and stored in document storage with a unique URL
7. Invoice record is written to the billing database with status `FINALIZED` and an immutable timestamp
8. `billing.invoice.finalized` event is published to the event bus with the invoice ID and total amount

## Controls

- Invoice generation must be idempotent for a given account and billing period; duplicate generation attempts must return the existing invoice
- Any invoice with a line item that cannot be traced to a source usage event or plan configuration must be blocked from finalization
- Invoice generation failures must be logged with sufficient context for reprocessing without data loss
