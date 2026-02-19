---
id: STANDARD-002
type: standard
title: Transaction Logging Standard
status: deprecated
owner: Security Lead
created: '2025-02-05T22:00:54.091Z'
updated: '2025-09-28T10:13:55.170Z'
tags:
  - standard
  - payment-processing
summary: Transaction Logging Standard
related_policies:
  - POLICY-001
  - POLICY-002
example: true
related_systems:
  - SYSTEM-001
  - SYSTEM-002
---

## Area

This standard governs the logging of all payment transaction events across the payment processing platform. It applies to every service that initiates, processes, updates, or finalizes a payment transaction, including the payment gateway service, fraud detection service, and settlement reconciliation jobs. Logs produced under this standard are used for incident investigation, compliance audits, and financial reconciliation.

## Controls

- Every transaction event must emit a structured log entry containing: transaction ID, timestamp (ISO 8601 UTC), event type, amount, currency, gateway provider, and outcome code
- Cardholder data (PAN, CVV, expiry) must never appear in log output; only the last four digits of the card number are permitted
- Transaction logs must be written to an append-only log store with a minimum retention period of 13 months
- Log entries must include a correlation ID linking all events within a single payment session for end-to-end traceability
- Log ingestion failures must trigger an alert within 5 minutes; the payment service must not silently drop log events
- All log stores must be protected with access controls limiting read access to authorized roles only

## Compliance Mappings

- PCI DSS Requirement 10: Maintain a log of all access to system components and cardholder data
- SOC 2 CC7.2: Monitor system components for anomalous behavior using logging
- ISO 27001 A.12.4: Logging and monitoring of system events

## Related Policies

- [[POLICY-002|PCI DSS Compliance Policy]]
