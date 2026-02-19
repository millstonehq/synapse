---
id: STANDARD-014
type: standard
title: SKU Naming Convention Standard
status: approved
owner: Compliance Officer
created: '2024-12-16T23:06:20.323Z'
updated: '2026-04-25T01:23:10.019Z'
tags:
  - standard
  - inventory-management
summary: SKU Naming Convention Standard
related_policies:
  - POLICY-015
  - POLICY-011
example: true
related_systems:
  - SYSTEM-011
  - SYSTEM-014
---

## Area

This standard defines the format, structure, and validation rules for Stock Keeping Unit (SKU) identifiers used across the inventory platform, warehouse systems, supplier integrations, and customer-facing product catalogs. A consistent SKU naming scheme is foundational to accurate inventory tracking, reporting, and cross-system reconciliation.

## Controls

- SKU identifiers must follow the format: `[CATEGORY]-[SUPPLIER]-[PRODUCT_CODE]-[VARIANT]`, where each segment is uppercase alphanumeric and hyphen-separated (e.g., `ELEC-ACME-HDPH200-BLK`)
- Category codes must be drawn from the approved category taxonomy maintained in the SKU Registry Service; ad-hoc category codes are prohibited
- SKU length must not exceed 32 characters; minimum length is 8 characters
- SKUs must be globally unique across all warehouses; duplicate SKU identifiers are rejected at the API layer
- Variant suffixes must use the standardized variant codes (e.g., `BLK`, `WHT`, `RED` for color; `SM`, `MD`, `LG`, `XL` for size)
- Retired SKUs must be marked as `status: discontinued` and must not be reused for new products for a minimum of 5 years

## Compliance Mappings

- GS1 Standards: Alignment with GS1 GTIN structure for supplier-integrated SKUs
- ISO 8000: Data quality — unique, accurate identifiers as a data quality requirement
- Internal Product Catalog Governance Policy: Section 3.1 (Product identifier standards)

## Related Policies

- [[POLICY-015|Dead Stock Disposal Policy]]
- [[POLICY-011|Inventory Data Accuracy Policy]]
