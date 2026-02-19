---
id: POLICY-047
type: policy
title: Revenue Recognition Policy
status: approved
owner: CISO
created: '2025-02-26T22:02:12.425Z'
updated: '2026-03-08T09:05:52.841Z'
tags:
  - policy
  - billing-engine
summary: Revenue Recognition Policy
example: true
related_standards:
  - STANDARD-055
  - STANDARD-057
---

## Scope

This policy governs how and when revenue is recognized across all subscription, usage-based, and one-time billing models operated by the Billing Engine. It applies to the engineering platform as well as the finance and accounting functions that consume billing system outputs.

Revenue recognition rules apply at the point of service delivery, not at the point of payment or invoice generation. Systems that produce revenue-affecting events must conform to this policy.

## Rationale

- ASC 606 and IFRS 15 require that revenue be recognized when (or as) performance obligations are satisfied, not when cash is received
- Incorrect revenue recognition creates material misstatements in financial reports and exposes the company to audit findings
- Usage-based billing models require real-time or near-real-time metering accuracy to correctly recognize revenue in the period it is earned
- Multi-period contracts require systematic deferral and amortization logic that must be enforced at the platform level

## Policy Statements

- Revenue must not be recognized until the performance obligation (service delivery) is complete for the billing period
- Prepaid subscription revenue must be deferred and recognized ratably over the subscription term
- Usage-based revenue must be recognized in the period in which usage occurred, based on metered event timestamps
- Billing Engine systems must emit revenue recognition events to the financial ledger within 24 hours of period close
- Any manual revenue adjustments require dual approval from Finance and Engineering leadership and must be logged

## Related Standards

- [[STANDARD-055|Invoice Format Standard]]
- [[STANDARD-057|Usage Metering Standard]]
