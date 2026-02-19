---
id: STANDARD-006
type: standard
title: Payment Error Code Standard
status: review
owner: Security Lead
created: '2025-03-28T03:48:14.278Z'
updated: '2025-12-30T16:06:11.975Z'
tags:
  - standard
  - payment-processing
summary: Payment Error Code Standard
related_policies:
  - POLICY-003
  - POLICY-005
example: true
related_systems:
  - SYSTEM-003
  - SYSTEM-001
---

## Area

This standard defines the error code taxonomy and response structure for all payment API errors. It applies to internal payment services, external-facing APIs, and gateway adapter layers. Consistent error codes enable integrators to implement correct retry and fallback logic, reduce support burden, and allow observability tooling to classify and alert on failure categories accurately.

## Controls

- All payment error responses must use a structured JSON body with fields: `error_code` (enum), `error_message` (human-readable), `request_id`, and `retryable` (boolean)
- Error codes must be drawn exclusively from the approved payment error code registry; new codes require a review and merge to the registry before use
- Transient errors (network timeouts, gateway unavailability) must be marked `retryable: true`; permanent errors (invalid card, insufficient funds) must be marked `retryable: false`
- Internal error details, stack traces, and gateway raw responses must never be surfaced in API error responses
- HTTP status codes must be semantically correct: 402 for payment declined, 422 for validation failures, 503 for gateway unavailability, 409 for idempotency conflicts
- Error codes must be stable across API versions; deprecated codes must remain in the registry with a deprecation notice for a minimum of 12 months

## Compliance Mappings

- PCI DSS Requirement 6.5: Prevention of information leakage through error messages
- OWASP API Security Top 10: API9 Improper Assets Management — versioning and error detail exposure
- ISO 20022: Error handling conventions for payment message responses

## Related Policies

- [[POLICY-003|Payment Gateway Failover Policy]]
- [[POLICY-005|Payment Fraud Prevention Policy]]
