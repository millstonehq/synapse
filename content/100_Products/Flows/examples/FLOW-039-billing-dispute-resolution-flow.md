---
id: FLOW-039
type: flow
title: Billing Dispute Resolution Flow
status: approved
owner: QA Engineer
created: '2025-04-01T03:20:53.037Z'
updated: '2026-05-29T10:27:24.982Z'
tags:
  - flow
  - billing-engine
summary: Billing Dispute Resolution Flow
feature_area: Billing Engine
related_prds:
  - PRD-048
example: true
---

## Steps

### Step 1: Customer Submits Dispute

The customer navigates to the invoice in the Self-Service Billing Portal ([[PRD-048|PRD-048]]) and clicks "Dispute this charge." They select a dispute reason from a predefined list (incorrect usage quantity / tax calculation error / plan price incorrect / duplicate charge / other) and provide a free-text description of the issue. Optionally, they attach a supporting document (PDF or CSV, max 5MB). The dispute is submitted and assigned a dispute ID.

### Step 2: Automated Pre-Triage

On dispute submission, the Billing Engine runs an automated pre-triage check. For usage disputes, it fetches the raw usage aggregates for the disputed period and compares them against the invoiced quantities. For tax disputes, it re-runs the Avalara tax calculation with the current rates to check for discrepancies. If the automated check finds a clear error (quantity mismatch > 1% or tax recalculation differs by > $0.01), the dispute is flagged as `auto_resolvable` and routed to the Customer Success queue with the pre-triage findings attached.

### Step 3: Customer Success Review

A Customer Success representative picks up the dispute from the Billing Admin Console ([[PRD-048|PRD-048]]) dispute queue. They review the pre-triage findings, the original invoice line items, and any attached documentation. If the dispute is valid, they initiate a credit note for the disputed amount. If the dispute requires a corrected invoice, they void the original invoice and trigger a re-issue with the corrected amounts.

### Step 4: Credit or Invoice Correction

For valid disputes, the CS rep issues a credit note via the Billing Admin Console. Credits above $500 require Finance team approval before being applied. The credit is recorded in the internal double-entry ledger as a debit to Revenue and a credit to Refund Expense, maintaining the ledger balance invariant. The customer's Stripe account is credited for the approved amount.

### Step 5: Resolution Notification

The customer receives an email notification summarizing the dispute resolution: whether the dispute was accepted or rejected, the amount credited if applicable, and when the credit will appear on their next invoice. The dispute record in the system is updated to `resolved` with a resolution note.

## Expected Results

- Dispute is acknowledged with a dispute ID within 60 seconds of submission
- Automated pre-triage is completed within 5 minutes of submission for usage and tax disputes
- Customer Success responds to all disputes within 4 business hours (SLA target)
- Approved credits appear on the customer's next invoice or as an account balance credit
- Customer receives an email notification upon resolution within 30 minutes of the CS rep marking the dispute resolved

## User Info

| Field | Value |
|-------|-------|
| Role | Customer (submitting) / Customer Success Rep (resolving) |
| Customer permissions | billing:read, dispute:create |
| CS Rep permissions | billing:write, credit:create (limits apply) |
| Test account | test-dispute-account@example.com (staging) |
| Environment | Staging |
