---
id: CAPABILITY-002
type: capability
title: Payment Compliance Capability
status: approved
owner: Head of Engineering
created: '2025-08-01T05:02:59.210Z'
updated: '2026-05-09T11:32:28.514Z'
tags:
  - capability
  - payment-processing
summary: Payment Compliance Capability
evidence_links:
  - PROCESS-001
  - STANDARD-006
  - STANDARD-005
example: true
---

## Domain

- Payment Processing
- Regulatory Compliance
- Security

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No formal PCI DSS controls. Raw card data handled directly. No audit logging.
- **Level 1 - Ad hoc**: Some PCI awareness but controls inconsistently applied. SAQ not completed. No formal data retention policy.
- **Level 2 - Repeatable**: PCI SAQ A completed using Stripe Elements for tokenization. Basic audit logging. Annual review but not operationalized.
- **Level 3 - Defined** (current): PCI SAQ A certified annually. 7-year data retention policy enforced. Payment audit trail via immutable `payment_events` table. Quarterly compliance review process in place. Staff trained on PCI requirements.
- **Level 4 - Managed**: Automated compliance evidence collection. Continuous monitoring for PCI control deviations. Automated alerts for anomalous payment patterns. Chargeback rate tracked as a compliance indicator.
- **Level 5 - Optimizing**: Real-time compliance posture dashboard. Automated pre-deploy PCI impact assessment for any change touching payment data. Sub-0.05% fraud rate maintained through continuous ML model updates.

**Gap to Level 4**: Need to automate PCI evidence collection (currently a manual process during annual audit), implement continuous monitoring alerts for out-of-scope card data exposure, and add chargeback rate to the weekly compliance metrics report.

## Metrics

- PCI DSS certification: Current level SAQ A, valid through Q4 2025
- Data retention compliance: 100% of payment records retained per 7-year policy (automated archival)
- Chargeback rate: Currently 0.12%, target < 0.10% (industry benchmark for card-not-present)
- Fraud false positive rate: Currently 0.8% of legitimate transactions flagged, target < 0.5%
- Audit log completeness: 100% of payment state changes captured in `payment_events`
- Compliance review cadence: Quarterly (on schedule)

## Evidence Links

- [[PROCESS-001|Compliance Review Process]] - Quarterly compliance review workflow
- [[STANDARD-006|PCI DSS Controls Standard]] - Specific PCI DSS 4.0 control mappings
- [[STANDARD-005|Data Classification Standard]] - Payment data classification and handling rules

## Notes

The organization completed the PCI DSS SAQ A certification in Q3 2025 using Stripe Elements for card tokenization. This keeps us in the simplest PCI tier by ensuring raw card data never reaches our servers.

Key improvements needed for Level 4:
- Automate the annual PCI evidence collection process — currently requires ~2 days of manual effort by the security team
- Add automated alerting if any code change introduces a code path that could expose card data (static analysis integration)
- Expand the quarterly compliance review to include chargeback trend analysis and fraud velocity metrics
