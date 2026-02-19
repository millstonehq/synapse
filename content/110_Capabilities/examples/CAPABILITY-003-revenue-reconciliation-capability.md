---
id: CAPABILITY-003
type: capability
title: Revenue Reconciliation Capability
status: approved
owner: Head of Engineering
created: '2024-03-24T16:27:09.984Z'
updated: '2026-12-23T03:32:26.858Z'
tags:
  - capability
  - payment-processing
summary: Revenue Reconciliation Capability
evidence_links:
  - PROCESS-005
  - STANDARD-005
  - POLICY-004
example: true
---

## Domain

- Payment Processing
- Financial Operations
- Analytics

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Level 0 - Initial**: No reconciliation process. Finance team manually compares gateway reports to internal records monthly. Discrepancies often undiscovered.
- **Level 1 - Ad hoc**: Nightly settlement batch job exists but silent failures go undetected. No alerting. Manual review required to verify.
- **Level 2 - Repeatable** (current): Nightly settlement batch job processes Stripe CSV. Automated alerting if batch job fails (INC-75 was the catalyst). Manual investigation of individual discrepancies. 48-hour resolution SLA for discrepancies.
- **Level 3 - Defined**: Automated discrepancy detection with categorized alerts (timing, amount, missing record). Defined resolution workflow with owner assignment. Discrepancy rate tracked as a KPI. Sub-24-hour resolution SLA.
- **Level 4 - Managed**: Real-time reconciliation stream (not batch). Discrepancy rate below 0.01%. Automated resolution for the most common discrepancy types. Finance dashboard shows live reconciliation status.
- **Level 5 - Optimizing**: Near-real-time reconciliation across all gateways and currencies. ML-based anomaly detection catches discrepancies before the finance team notices.

**Gap to Level 3**: Need to categorize discrepancy types in the settlement job output, implement an owner-assignment workflow for discrepancy tickets, and move the discrepancy rate metric into the weekly dashboard.

## Metrics

- Settlement batch success rate: Currently 99.7% (3 failures in past year, all resolved within 24 hours)
- Discrepancy rate: Currently 0.03% of transactions have a settlement discrepancy
- Mean time to resolve discrepancy: Currently 26 hours, target < 24 hours
- Settlement batch completion time: Currently 28 minutes for ~50,000 transactions, target < 30 minutes SLA
- Uncategorized discrepancies: Currently 40% are "unknown cause", target < 10%

## Evidence Links

- [[PROCESS-005|Settlement Reconciliation Process]] - Nightly batch execution and discrepancy resolution workflow
- [[STANDARD-005|Financial Reporting Standard]] - Requirements for revenue reporting accuracy and retention
- [[POLICY-004|Financial Data Policy]] - Data handling and access controls for settlement data

## Notes

The settlement silent failure incident (INC-75, September 2024) was a turning point: the misconfigured SQS DLQ ARN caused 4,200 transactions to remain in `captured` state overnight with no alert firing. As a result, the team added explicit alerting on settlement batch completeness (transactions settled per run < 1000 triggers a P1 alert).

Key improvements needed for Level 3:
- Categorize discrepancy types in the settlement job output: "timing" (settlement pending gateway), "amount" (partial capture discrepancy), "missing" (transaction in our system not in gateway report)
- Implement an automated Jira ticket for each discrepancy batch with daily reminders until resolved
- Add discrepancy rate and mean resolution time to the weekly payment team KPI report
