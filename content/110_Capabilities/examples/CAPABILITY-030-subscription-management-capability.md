---
id: CAPABILITY-030
type: capability
title: Subscription Management Capability
status: approved
owner: Head of Engineering
created: '2024-09-07T04:18:04.092Z'
updated: '2026-12-13T09:32:34.211Z'
tags:
  - capability
  - billing-engine
summary: Subscription Management Capability
evidence_links:
  - POLICY-046
  - STANDARD-056
  - POLICY-047
example: true
---

## Domain

- Subscription Lifecycle Management (create, trial, activate, upgrade, pause, cancel)
- Billing Period Management and Renewal
- Plan and Pricing Configuration

## Maturity (0-5)

- Subscription state machine: 4/5 - Formal state machine with explicit transitions, audit log, and Stripe sync; distributed lock prevents race conditions
- Plan and pricing configuration: 3/5 - Plans configurable via API; no self-serve plan builder; changes require engineering involvement
- Trial management: 3/5 - Trial period supported; automated trial expiry notification is manual (CS-triggered)
- Pause and resume: 3/5 - Pause state implemented; pause duration limits and auto-resume not yet enforced
- Self-service subscription changes: 2/5 - Customers cannot upgrade/downgrade without CS involvement; Self-Service Portal (PRD-046) in development

## Metrics

- Active subscriptions: ~12,000 (growing 8% MoM)
- Involuntary churn (payment failure): 2.1% of renewals (target < 1.5%)
- Voluntary churn: 1.8% monthly (target < 1.5%)
- Trial-to-paid conversion rate: 34% (target: 40%)
- Subscription state divergence (internal vs Stripe): < 0.1% (measured by daily reconciliation job)

## Evidence Links

- [[POLICY-046|Subscription Data Retention Policy]] - Data retention requirements for subscription history
- [[STANDARD-056|Subscription State Standard]] - Controls for allowable subscription states and transitions
- [[POLICY-047|Pricing Change Policy]] - Governance for plan price changes and customer notification requirements

## Notes

- The subscription state machine was rebuilt in Q2 2024 with explicit state enumeration and an audit log; prior implicit state management was the source of several billing errors
- Key improvement areas: self-service plan changes (addresses high CS volume), automated trial conversion nudges, and dunning optimization to reduce involuntary churn
- Stripe subscription divergence is monitored by a daily reconciliation job; discrepancies trigger a Slack alert and are resolved within 24 hours
