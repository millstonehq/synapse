---
id: POLICY-004
type: policy
title: Chargeback Handling Policy
status: approved
owner: CTO
created: '2025-01-19T21:49:55.601Z'
updated: '2026-11-29T15:43:59.999Z'
tags:
  - policy
  - payment-processing
summary: Chargeback Handling Policy
example: true
related_standards:
  - STANDARD-003
  - STANDARD-001
---

## Scope

This policy applies to all payment transactions processed through the platform that result in a chargeback or pre-arbitration dispute filed by a cardholder or issuing bank. It covers the engineering systems that store transaction evidence, the operations team that manages dispute submissions, and the finance team that tracks chargeback liability.

## Rationale

- Unresponded chargebacks result in automatic liability and financial loss; timely response is essential
- Chargeback ratios above card network thresholds (typically 1%) trigger fines and potential loss of processing rights
- Maintaining complete transaction evidence enables successful dispute representments and reduces net chargeback losses
- A consistent handling process reduces manual effort and ensures compliance with card network dispute deadlines

## Policy Statements

- All payment transactions must retain evidence records (authorization response, fulfillment confirmation, customer consent) for a minimum of 18 months
- Chargeback notifications must be acknowledged and triaged within 24 hours of receipt
- Dispute representment packages must be submitted within card network deadlines (typically 10-20 calendar days from notification)
- Monthly chargeback ratios must be monitored; any ratio exceeding 0.5% triggers an immediate review by the Payments team
- Engineering systems must provide automated evidence export capabilities to support dispute submissions
- All chargeback outcomes and financial impacts must be logged and reported to Finance monthly

## Related Standards

- [[STANDARD-003|Payment Encryption Standard]]
