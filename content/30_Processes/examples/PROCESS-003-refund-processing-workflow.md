---
id: PROCESS-003
type: process
title: Refund Processing Workflow
status: draft
owner: Director of Engineering
created: '2024-06-22T12:35:28.269Z'
updated: '2026-07-25T17:12:43.286Z'
tags:
  - process
  - payment-processing
summary: Refund Processing Workflow
related_standards:
  - STANDARD-002
  - STANDARD-006
related_sops:
  - SOP-006
  - SOP-002
related_systems:
  - SYSTEM-004
example: true
---

## Purpose

This process governs the lifecycle of payment refunds from initiation through gateway processing to confirmation on the customer's payment method. It ensures that refunds are authorized at the appropriate level, executed idempotently to prevent duplicate credits, and tracked to completion with full audit trails. Consistent refund processing reduces customer complaints and chargeback risk.

## Scope

- Full and partial refunds on settled transactions
- Automated refund flows triggered by cancellation and return events
- Manual refund requests submitted by Customer Support
- Failed refund investigation and reprocessing

## Roles and Responsibilities

- **Payments Engineer**: Maintains the refund service and handles technical escalations for stuck or failed refunds
- **Customer Support Agent**: Initiates manual refunds within approved value limits using the internal tooling
- **Finance Analyst**: Approves refunds exceeding the automated approval threshold and monitors refund rates
- **On-Call Engineer**: Responds to refund service alerts and investigates gateway-side refund failures

## Triggers

- Customer-initiated cancellation or return event triggers automated refund
- Customer Support agent submits a manual refund request via internal tooling
- Dispute pre-arbitration notification triggers refund as a chargeback prevention action
- Automated fraud review result reverses a captured charge

## Inputs

- Original transaction ID and capture confirmation
- Refund amount (full or partial) and reason code
- Authorization from Finance for refunds exceeding $500
- Customer notification preference (email, in-app)

## Outputs

- Refund transaction record with refund ID, amount, status, and gateway confirmation
- Customer notification confirming refund initiation and expected timeline
- Updated transaction record linking original charge to refund
- Finance notification for refunds exceeding approval thresholds

## Steps

1. Refund request is received via API, internal tooling, or automated event; request is validated against the original transaction
2. Idempotency check performed using refund request ID to prevent duplicate processing
3. Authorization check: refunds under $500 are auto-approved; refunds $500-$5,000 require Customer Support manager approval; refunds over $5,000 require Finance Analyst approval
4. Approved refund is submitted to the payment gateway using the original payment method token
5. Gateway response is recorded: success triggers customer notification and ledger update; failure triggers retry with exponential backoff
6. After three failed gateway attempts, refund is moved to manual investigation queue and on-call is notified
7. Successful refunds are confirmed to the customer with expected timeline (typically 3-7 business days)
8. Refund record is finalized in the ledger upon gateway settlement confirmation

## Controls

- All refunds must be linked to an original captured transaction; refunds without a matching original are rejected
- Refund amount must not exceed the original captured amount
- Duplicate refund prevention is enforced by the idempotency store per [[STANDARD-006|Payment Error Code Standard]]
- Refund audit logs must capture requester identity, approval chain, and all gateway interaction timestamps
