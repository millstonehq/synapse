---
id: STANDARD-017
type: standard
title: Stock Movement Logging Standard
status: approved
owner: Compliance Officer
created: '2024-10-03T19:47:41.306Z'
updated: '2026-08-25T03:46:24.258Z'
tags:
  - standard
  - inventory-management
summary: Stock Movement Logging Standard
related_policies:
  - POLICY-011
  - POLICY-013
example: true
related_systems:
  - SYSTEM-012
  - SYSTEM-015
---

## Area

This standard defines the mandatory fields, retention requirements, and integrity constraints for logging all stock movements within the inventory platform. Stock movement logs provide the audit trail required for financial reconciliation, discrepancy investigation, and regulatory compliance across all warehouse operations.

## Controls

- Every stock movement (inbound receipt, outbound shipment, internal transfer, adjustment, return, write-off) must generate a log entry before the quantity change is committed to the inventory database
- Required log fields: `movement_id` (UUID v4), `sku_id`, `warehouse_id`, `movement_type` (enum), `quantity_delta` (signed integer), `quantity_before`, `quantity_after`, `reference_id` (order/receipt/transfer ID), `initiated_by` (user or service account ID), `occurred_at` (ISO 8601 UTC)
- Log entries must be written to an append-only store; updates or deletions of movement log records are prohibited
- Movement logs must be indexed on `sku_id + occurred_at` and `warehouse_id + occurred_at` to support efficient discrepancy queries
- Negative quantity results (`quantity_after < 0`) must be rejected at write time with a validation error; this indicates a system integrity failure
- Movement logs must be exported to cold storage within 90 days and retained per the Warehouse Data Retention Policy

## Compliance Mappings

- SOC 2: CC5.2 (Select and develop control activities) — immutable audit log as a key control
- ISO 27001: A.12.4.3 (Administrator and operator logs) — movement log integrity requirements
- Internal Financial Controls Framework: Section 7 (Inventory audit trail)

## Related Policies

- [[POLICY-011|Inventory Data Accuracy Policy]]
- [[POLICY-013|Warehouse Data Retention Policy]]
