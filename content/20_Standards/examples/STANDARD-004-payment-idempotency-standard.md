---
id: STANDARD-004
type: standard
title: Payment Idempotency Standard
status: approved
owner: Head of Engineering
created: '2025-08-18T08:07:49.013Z'
updated: '2026-07-04T10:17:38.464Z'
tags:
  - standard
  - payment-processing
summary: Payment Idempotency Standard
related_policies:
  - POLICY-005
  - POLICY-004
example: true
related_systems:
  - SYSTEM-002
  - SYSTEM-004
---

## Area

This standard defines requirements for idempotent payment operations across the platform. It applies to all payment initiation, capture, refund, and cancellation endpoints. Idempotency controls prevent duplicate charges that can result from network retries, client timeouts, or infrastructure failures, and are critical for maintaining accurate financial records and preventing customer disputes.

## Controls

- All payment mutation endpoints must accept an idempotency key supplied by the caller as a request header
- Idempotency keys must be persisted for a minimum of 24 hours; repeated requests with the same key within that window must return the original response without re-executing the operation
- Idempotency key namespacing must be per-merchant or per-integration to prevent cross-tenant key collisions
- The idempotency store must be checked before any external gateway call is made; gateway calls must not precede idempotency validation
- Responses to duplicate idempotent requests must be byte-for-byte identical to the original response, including status code and body
- Idempotency store failures must cause the request to fail safely with a 503 rather than allow a potentially duplicate charge to proceed

## Compliance Mappings

- PCI DSS Requirement 6.4: Address common coding vulnerabilities including duplicate transaction handling
- ISO 20022 Payment Message Standards: Deduplication requirements for payment instructions
- SOC 2 CC6.1: Logical and physical access controls supporting transaction integrity

## Related Policies

- [[POLICY-005|Payment Fraud Prevention Policy]]
- [[POLICY-004|Chargeback Handling Policy]]
