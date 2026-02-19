---
id: STANDARD-060
type: standard
title: Currency Handling Standard
status: draft
owner: Head of Engineering
created: '2025-05-11T01:07:02.209Z'
updated: '2026-09-26T02:25:33.871Z'
tags:
  - standard
  - billing-engine
summary: Currency Handling Standard
related_policies:
  - POLICY-050
  - POLICY-049
example: true
related_systems:
  - SYSTEM-048
  - SYSTEM-049
---

## Area

This standard defines how currencies are represented, stored, converted, and displayed throughout the Billing Engine. It applies to all services that handle monetary values including pricing, invoicing, payment processing, and reporting.

Consistent currency handling prevents rounding errors, eliminates ambiguity in multi-currency environments, and ensures financial reports are accurate across all supported locales.

## Controls

- All monetary amounts must be stored as integers in the smallest currency unit (e.g., cents for USD, pence for GBP); floating-point types must never be used for currency storage
- Currency codes must conform to ISO 4217 (three-letter uppercase codes); any unsupported currency must cause the transaction to be rejected with an explicit error
- Currency conversion must use exchange rates from the authoritative rate service; rates must be timestamped and the rate used for any conversion must be stored alongside the converted amount
- Rounding for invoice totals must use "half-up" rounding (banker's rounding is not permitted for customer-facing amounts)
- Multi-currency invoices are not permitted; each invoice must be denominated in a single currency, which is the customer's billing currency at account creation time

## Compliance Mappings

- SOC 2 CC4.2: Financial data integrity controls require deterministic currency arithmetic throughout the billing pipeline
- IFRS 21 / ASC 830: Foreign currency transactions must be translated at spot rates on the transaction date; gains/losses must be separately tracked
- PCI-DSS 4.1: Currency transmission in payment flows must use approved cryptographic standards regardless of currency

## Related Policies

- [[POLICY-050|Billing Access Control Policy]]
- [[POLICY-049|Invoice Retention Policy]]
