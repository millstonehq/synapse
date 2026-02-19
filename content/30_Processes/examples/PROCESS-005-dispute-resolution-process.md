---
id: PROCESS-005
type: process
title: Dispute Resolution Process
status: draft
owner: Engineering Manager
created: '2024-06-20T02:06:09.078Z'
updated: '2026-11-27T02:37:45.291Z'
tags:
  - process
  - payment-processing
summary: Dispute Resolution Process
related_standards:
  - STANDARD-004
  - STANDARD-001
related_sops:
  - SOP-006
  - SOP-009
related_systems:
  - SYSTEM-005
example: true
---

## Purpose

This process manages the lifecycle of payment disputes, from initial notification through representment or acceptance, to final resolution. It ensures that disputes are handled within card network deadlines, that transaction evidence is compiled accurately, and that outcomes are tracked for financial reporting and chargeback ratio management.

## Scope

- Chargebacks filed by cardholders through their issuing bank
- Pre-arbitration and arbitration phases for escalated disputes
- Retrieval requests (information requests prior to formal chargeback)
- Friendly fraud disputes where representment is commercially viable

## Roles and Responsibilities

- **Dispute Operations Analyst**: Receives dispute notifications, compiles evidence packages, and submits representments
- **Payments Engineer**: Provides technical evidence exports and assists with transaction trace reconstruction
- **Finance Analyst**: Tracks dispute liability, approves acceptance decisions on non-viable representments, and reports chargeback ratios
- **Legal Counsel**: Advises on disputes involving regulatory complaints or amounts requiring legal escalation

## Triggers

- Dispute notification received via gateway webhook or settlement file
- Retrieval request received from issuing bank via gateway portal
- Internal alert triggered when chargeback ratio approaches 0.5% threshold
- Customer contacts support alleging unauthorized charge prior to formal dispute filing

## Inputs

- Dispute notification with chargeback reason code and deadline
- Original transaction record including authorization, capture, and fulfillment evidence
- Customer interaction history relevant to the disputed transaction
- Prior dispute history for the cardholder (used for representment strategy)

## Outputs

- Submitted representment package or accepted liability decision
- Dispute outcome record linked to the original transaction
- Updated chargeback ratio metrics for Finance reporting
- Escalation ticket to Legal for disputes exceeding $10,000 or involving regulatory claims

## Steps

1. Dispute notification is received and automatically logged in the dispute management system with deadline calculation
2. Transaction evidence is automatically compiled: authorization response, capture confirmation, fulfillment record, customer consent
3. Dispute Operations Analyst reviews the reason code and evidence to determine representment viability
4. For viable representments: compile the full evidence package and submit via gateway representment portal before the deadline
5. For non-viable disputes: Finance Analyst approves acceptance; dispute is closed with liability accepted
6. Track representment outcome: won disputes are closed; lost disputes trigger arbitration assessment
7. Finance Analyst updates chargeback ratio tracker; trigger review process if ratio exceeds 0.5%
8. Monthly dispute summary is reported to Finance VP and Platform Lead

## Controls

- Disputes must be acknowledged within 24 hours of notification to ensure deadline compliance
- Representment submissions require review by both Dispute Operations Analyst and Finance Analyst for disputes over $1,000
- All dispute evidence packages are archived for 18 months per card network requirements
- Chargeback ratio is reviewed weekly; ratio above 0.75% triggers escalation to VP Engineering
