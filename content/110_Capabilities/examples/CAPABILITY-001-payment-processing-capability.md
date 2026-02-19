---
id: CAPABILITY-001
type: capability
title: Payment Processing Capability
status: draft
owner: VP Engineering
created: '2024-10-30T11:26:31.176Z'
updated: '2025-04-10T23:35:26.928Z'
tags:
  - capability
  - payment-processing
summary: Payment Processing Capability
evidence_links:
  - STANDARD-002
  - PROCESS-004
  - STANDARD-001
example: true
---

## Domain

- Payment Processing
- Commerce
- Financial Operations

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: All payments processed manually by operations staff via gateway dashboard. No API. No audit trail.
- **Level 1 - Ad hoc**: Basic payment API exists but no idempotency, no failover, no monitoring. Duplicate charges occur occasionally.
- **Level 2 - Repeatable**: Idempotency implemented. Single gateway (Stripe). Manual failover process. Basic alerting on error rate.
- **Level 3 - Defined** (current): Multi-gateway with automatic circuit breaker failover. Idempotency enforced. SLOs defined and monitored. Incident runbooks in place. PCI SAQ A compliant.
- **Level 4 - Managed**: Real-time fraud scoring integrated. Gateway cost optimization via smart routing. Automated reconciliation with < 0.01% discrepancy. Proactive capacity scaling.
- **Level 5 - Optimizing**: ML-driven fraud prevention with < 0.05% false positive rate. Multi-region payment processing for latency optimization. Near-zero manual intervention in payment operations.

**Gap to Level 4**: Need to complete fraud scoring integration (currently P3 in backlog), implement gateway cost routing to reduce blended transaction rate, and automate the nightly reconciliation batch with real-time alerting.

## Metrics

- Payment success rate: Currently 99.1%, target > 99.5% (excluding customer-side declines)
- P95 authorization latency: Currently 680ms, target < 500ms
- Monthly availability: Currently 99.89%, target 99.9%
- Gateway failover time: Currently ~90 seconds, target < 60 seconds
- Chargeback rate: Currently 0.12%, target < 0.10%
- Reconciliation discrepancy rate: Currently 0.03%, target < 0.01%

## Evidence Links

- [[STANDARD-002|Payment Processing Standard]] - Controls and compliance mappings for PCI SAQ A
- [[STANDARD-001|Data Retention Standard]] - 7-year retention requirement for payment records
- [[PROCESS-004|Change Management Process]] - Controls for payment system changes

## Notes

The capability reached Level 3 with the launch of the Payments API v1 in Q2 2025, which introduced multi-gateway support and automated failover. The two SEV-2 incidents in Q1 2025 (INC-72 and INC-76) identified gaps in fraud scoring and circuit breaker threshold tuning that are now addressed.

Key improvements needed for Level 4:
- Integrate Fraud Detection Service scoring into the authorization path (currently a separate async process)
- Implement gateway selection logic that routes based on cost and availability, not just a fixed primary/secondary model
- Automate the nightly settlement reconciliation with same-day alerting on discrepancies
