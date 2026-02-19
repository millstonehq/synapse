---
id: PROCESS-061
type: process
title: Payment Compliance Review Process
status: deprecated
owner: Platform Lead
created: '2025-09-23T19:59:40.233Z'
updated: '2025-10-12T02:51:00.629Z'
tags:
  - process
  - payment-processing
summary: Payment Compliance Review Process
related_standards:
  - STANDARD-004
  - STANDARD-003
related_sops:
  - SOP-006
  - SOP-004
related_systems:
  - SYSTEM-002
example: true
---

## Purpose

Ensure the payment platform maintains continuous PCI DSS SAQ A compliance and that all changes with compliance implications are reviewed before deployment. This process governs quarterly compliance reviews, annual PCI DSS self-assessment, and the compliance gate for changes that touch payment data scope. It is the operational workflow for the Payment Compliance Capability.

## Scope

All activities related to payment platform PCI DSS compliance, including:

- Quarterly review of PCI DSS controls and evidence
- Annual PCI DSS SAQ A self-assessment and attestation
- Compliance impact assessment for changes to payment systems, including [[SYSTEM-002|Transaction Ledger Service]]
- Tracking and remediation of compliance findings
- Payment data scope review when new features are introduced

**Out of scope:** General change management (covered by the change management process), non-payment system compliance, and SOC 2 controls.

## Roles and Responsibilities

- **Compliance Owner** - The security team lead. Responsible for: scheduling quarterly reviews, maintaining the control evidence inventory, coordinating the annual SAQ A, and communicating compliance status to the CTO.
- **Payments Tech Lead** - Responsible for: reviewing compliance impact of payment system changes, ensuring PCI controls are implemented correctly in code, and providing technical evidence for SAQ A.
- **Change Author** - Any engineer making a change to payment systems. Responsible for: completing the compliance impact checklist before merging changes that affect payment scope.
- **Finance Lead** - Responsible for: reviewing reconciliation controls during quarterly reviews and signing off on the financial reporting section of the SAQ A.

## Triggers

- Quarterly: Calendar trigger on the first week of each quarter
- Annual: Calendar trigger in October for Q4 SAQ A preparation
- Ad hoc: Any change to payment systems that modifies how card data flows, where payment data is stored, or what third-party services are involved

## Inputs

- PCI DSS 4.0 SAQ A checklist (maintained in the security team's Confluence space)
- Control evidence inventory: logs showing TLS configuration, MFA status, Stripe Elements CSP headers, access control records
- Change inventory for the quarter: all PRs merged to payment system repositories
- Previous quarter's compliance review findings and their remediation status

## Outputs

- Quarterly compliance review report with control status (green/amber/red) for each SAQ A requirement
- Updated control evidence inventory
- Findings list with owner, severity, and remediation deadline
- Annual: Completed PCI DSS SAQ A and Attestation of Compliance (AoC) signed by the CTO
- Annual: Updated scope definition document confirming which systems are in scope

## Steps

1. **Compliance Owner** schedules the quarterly review 2 weeks in advance. Sends calendar invites to Payments Tech Lead and Finance Lead.
2. **Compliance Owner** collects evidence for the 12 SAQ A controls: runs the evidence collection script to pull TLS config, MFA enrollment status, CSP headers, and access control exports.
3. **Payments Tech Lead** reviews the change inventory for the quarter and identifies any changes that modified payment scope. For each scoped change, confirms that the compliance impact checklist was completed before merge.
4. **Compliance Owner** and **Payments Tech Lead** conduct the 60-minute quarterly review meeting. Work through the control checklist, marking each control as green (compliant), amber (remediation needed within 30 days), or red (critical finding, immediate action required).
5. **Finance Lead** reviews the reconciliation controls section: confirms that the [[SYSTEM-002|Transaction Ledger Service]] audit trail is intact, settlement batch alerts are active, and discrepancy rate is within the 0.01% target.
6. **Compliance Owner** documents findings and assigns owners and deadlines. Red findings are escalated to the CTO within 24 hours.
7. **Compliance Owner** publishes the quarterly review report to the compliance Confluence page within 5 business days.
8. **Annual only**: Compliance Owner prepares the PCI DSS SAQ A questionnaire responses based on the four quarterly reviews. Payments Tech Lead provides technical attestation. CTO signs the AoC.

## Controls

- Quarterly reviews must be completed within 30 days of the quarter end — no skips
- Red findings must have a remediation plan within 24 hours and be resolved within 7 days
- Amber findings must be resolved within 30 days
- Any change adding a new third-party service to the payment checkout path requires Compliance Owner pre-approval
- SAQ A must be completed and signed before the annual PCI DSS certification expiry date
- Compliance review records retained for 7 years per PCI DSS requirement 12.5.2
