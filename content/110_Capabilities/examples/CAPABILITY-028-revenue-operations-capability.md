---
id: CAPABILITY-028
type: capability
title: Revenue Operations Capability
status: accepted
owner: VP Engineering
created: '2025-01-19T05:21:16.731Z'
updated: '2026-02-18T08:23:18.410Z'
tags:
  - capability
  - billing-engine
summary: Revenue Operations Capability
evidence_links:
  - POLICY-049
  - STANDARD-058
  - STANDARD-057
example: true
---

## Domain

- Billing and Revenue Operations
- Financial Reporting
- Subscription Lifecycle Management

## Maturity (0-5)

- Revenue recognition accuracy: 3/5 - Double-entry ledger is implemented; ASC 606 deferral logic is not yet automated
- MRR/ARR reporting: 3/5 - Live data available; forecasting relies on manual spreadsheet processes
- Billing operations tooling: 2/5 - CS team still uses direct Stripe dashboard for many operations; Admin Console in development
- Usage-based revenue metering: 4/5 - Usage Metering Service is production-stable with SUM/MAX aggregation; LAST function in progress
- Dunning and payment recovery: 2/5 - Stripe handles basic dunning; no custom retry logic or cohort-based recovery strategy

## Metrics

- Monthly invoice error rate: 0.3% (target < 0.1%)
- Billing-related support ticket volume: 400/month (target < 160/month)
- Revenue reconciliation discrepancy rate: 1.2% of invoices require manual correction (target < 0.5%)
- MRR forecast accuracy (3-month): within 8% of actual (target: within 5%)
- Time to resolve billing dispute: 3 days median (target: < 4 hours)

## Evidence Links

- [[POLICY-049|Revenue Operations Policy]] - Organizational mandate for billing accuracy and revenue reporting
- [[STANDARD-058|Invoice Content Standard]] - Controls for invoice formatting and required fields
- [[STANDARD-057|Revenue Reporting Standard]] - Controls for MRR/ARR calculation methodology

## Notes

- The transition to usage-based pricing in Q3 2024 significantly increased billing complexity; the revenue operations capability maturity has not kept pace
- The primary gaps are in tooling (Billing Admin Console) and automation (ASC 606 deferral); both are active initiatives
- Target state by end of year: Admin Console in production, Revenue Forecasting Tool live, billing dispute SLA met consistently
