---
id: STANDARD-005
type: standard
title: Payment Webhook Standard
status: approved
owner: Head of Engineering
created: '2024-01-11T10:12:18.429Z'
updated: '2026-03-07T07:10:41.501Z'
tags:
  - standard
  - payment-processing
summary: Payment Webhook Standard
related_policies:
  - POLICY-001
  - POLICY-005
example: true
related_systems:
  - SYSTEM-004
  - SYSTEM-005
---

## Area

This standard governs the design and delivery of payment event webhooks sent from the platform to merchant and partner integrations. It covers event payload structure, delivery guarantees, signature verification, retry behavior, and consumer acknowledgment requirements. Any service that emits or consumes payment lifecycle webhooks must conform to this standard.

## Controls

- All webhook payloads must be signed using HMAC-SHA256 with a per-endpoint shared secret; the signature must be included in the `X-Payment-Signature` header
- Webhook consumers must verify the signature before processing the payload; unsigned or invalid-signature payloads must be rejected with HTTP 401
- Event payloads must include: event ID, event type, timestamp, API version, and the full resource object at time of event
- Webhook delivery must use at-least-once semantics with exponential backoff retries; maximum retry window is 72 hours
- A webhook delivery is considered acknowledged only when the consumer responds with HTTP 2xx within 30 seconds; non-2xx or timeout responses trigger retry
- Event IDs must be used by consumers to deduplicate received events; consumers must implement idempotent processing

## Compliance Mappings

- PCI DSS Requirement 6.4: Secure external communications and API integrations
- OWASP API Security Top 10: API8 Injection and API3 Broken Object Level Authorization mitigations
- SOC 2 CC6.6: Logical access controls for external-facing integrations

## Related Policies

- [[POLICY-005|Payment Fraud Prevention Policy]]
