---
id: PROCESS-058
type: process
title: Billing Dispute Handling Process
status: approved
owner: Engineering Manager
created: '2025-09-21T20:37:48.508Z'
updated: '2025-11-17T07:18:55.932Z'
tags:
  - process
  - billing-engine
summary: Billing Dispute Handling Process
related_standards:
  - STANDARD-060
  - STANDARD-057
related_sops:
  - SOP-100
  - SOP-095
related_systems:
  - SYSTEM-049
example: true
---

## Purpose

The Billing Dispute Handling Process defines how billing disputes raised by customers or internal stakeholders are received, investigated, resolved, and closed. It ensures disputes are handled consistently, within defined SLA windows, and with full audit trail documentation.

This process covers disputes about invoice amounts, usage calculations, tax charges, payment failures attributable to billing errors, and incorrectly applied credits or promotions.

## Scope

- Customer-initiated disputes submitted via support channels
- Internally detected discrepancies from automated reconciliation jobs
- Disputes involving any billing model: subscription, usage-based, or one-time charges
- Escalations from Customer Support to the Billing Platform Engineering team

## Roles and Responsibilities

- **Customer Support Agent**: Receives initial dispute, gathers customer-provided evidence, and creates a dispute ticket; escalates to Engineering if technical investigation is required
- **Billing Platform Engineer**: Performs technical investigation of disputed charges by reviewing usage events, calculation logs, and pricing configurations
- **Engineering Manager**: Approves credits or adjustments above $1,000 or that affect multiple accounts; reviews and approves postmortem for systematic bugs
- **Finance Operations**: Validates credit amounts before issuance; ensures corrections are reflected in revenue reports

## Triggers

- Customer submits a dispute via the support portal or directly to their account manager
- Automated reconciliation job detects a discrepancy between metered usage and billed amounts exceeding the 0.1% threshold

## Inputs

- Dispute details: customer account ID, disputed invoice ID, disputed amount, customer explanation
- Customer-provided evidence (screenshots, usage exports, contract terms)
- Billing investigation access to usage event logs, invoice generation logs, and pricing configuration history

## Outputs

- Dispute resolution record: outcome (upheld, rejected, partially credited), root cause, and evidence
- Credit memo or adjustment invoice if a billing error is confirmed
- Postmortem ticket if the dispute reveals a systematic platform bug
- Closure notification to the customer with resolution explanation

## Steps

1. Customer Support creates a dispute ticket with account ID, invoice ID, disputed amount, and customer explanation
2. Support agent performs initial triage: checks if the invoice exists, if it is within the dispute window, and if the customer's concern is clearly stated
3. Billing Platform Engineer retrieves and reviews the invoice generation log, usage event aggregates, and applied pricing configuration for the disputed period
4. Engineer determines the root cause: billing calculation error, metering error, data entry error, or customer misunderstanding of pricing
5. If a billing error is confirmed, Engineer calculates the correct amount and prepares a credit memo or adjustment invoice for Finance Operations review
6. Finance Operations validates the credit amount and approves issuance
7. Engineering Manager approves credits above the $1,000 threshold
8. Credit is applied to the customer account and a resolution notification is sent; dispute ticket is closed with outcome documented

## Controls

- All disputes must receive an acknowledgment within one business day of creation
- Engineers must not directly modify finalized invoice records; credits must be issued as separate adjustment records
- Any dispute revealing a systematic calculation bug must trigger the postmortem process within 48 hours
