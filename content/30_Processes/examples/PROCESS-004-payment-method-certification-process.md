---
id: PROCESS-004
type: process
title: Payment Method Certification Process
status: approved
owner: Director of Engineering
created: '2025-05-02T05:37:05.940Z'
updated: '2026-03-20T23:48:33.330Z'
tags:
  - process
  - payment-processing
summary: Payment Method Certification Process
related_standards:
  - STANDARD-002
  - STANDARD-004
related_sops:
  - SOP-006
  - SOP-008
related_systems:
  - SYSTEM-001
example: true
---

## Purpose

This process certifies that a new payment method implementation meets the platform's technical, security, and compliance requirements before it is made available to merchants. Certification ensures that all payment method flows are thoroughly tested and that the implementation conforms to the relevant card network or scheme rules.

## Scope

- New card scheme integrations (e.g., Visa, Mastercard, Amex)
- Digital wallet payment methods (e.g., Apple Pay, Google Pay)
- Bank debit and credit transfer payment methods
- Buy-now-pay-later and alternative payment method integrations

## Roles and Responsibilities

- **Payments Engineer**: Implements the payment method and addresses certification findings
- **QA Lead**: Designs and executes the certification test suite including required scheme test cases
- **Security Engineer**: Reviews credential handling, tokenization, and data transmission for the new payment method
- **Compliance Officer**: Confirms applicable scheme rules and regulatory requirements are addressed
- **Platform Lead**: Issues final certification sign-off and approves production enablement

## Triggers

- Product roadmap milestone adds a new payment method to the platform
- Card network mandates adoption of a new protocol (e.g., 3D Secure 2.0)
- Merchant customer demand for a payment method not currently supported

## Inputs

- Payment method technical specification and scheme rules documentation
- Sandbox test credentials from the card network or payment method provider
- Security requirements checklist for the payment method type
- Idempotency and error handling requirements per [[STANDARD-004|Payment Idempotency Standard]]

## Outputs

- Certification test report with pass/fail status for all required test cases
- Security sign-off from Security Engineer
- Compliance checklist signed by Compliance Officer
- Production enablement ticket approved by Platform Lead

## Steps

1. Gather scheme test case documentation and configure sandbox environment with test credentials
2. Payments Engineer implements the payment method adapter and unit tests
3. QA Lead executes the mandatory test case matrix: authorization, capture, void, refund, and decline scenarios
4. Security Engineer reviews tokenization flow, credential storage, and API communication security
5. Compliance Officer reviews scheme rule adherence and any applicable regulatory requirements
6. Address any failures or findings identified in steps 3-5; re-test until all cases pass
7. Platform Lead reviews the certification report, security sign-off, and compliance checklist
8. Platform Lead issues certification approval; payment method is deployed behind a feature flag for controlled rollout

## Controls

- A payment method may not be exposed to merchants without a completed certification report
- All mandatory scheme test cases must achieve passing status; there are no waivers for scheme-required cases
- Security sign-off is a hard gate; certification cannot proceed with open security findings of high or critical severity
- Certification records are retained for 5 years per scheme and audit requirements
