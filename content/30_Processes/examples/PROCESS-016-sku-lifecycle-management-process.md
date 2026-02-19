---
id: PROCESS-016
type: process
title: SKU Lifecycle Management Process
status: review
owner: Engineering Manager
created: '2025-05-05T22:56:25.715Z'
updated: '2026-04-27T02:12:52.784Z'
tags:
  - process
  - inventory-management
summary: SKU Lifecycle Management Process
related_standards:
  - STANDARD-017
  - STANDARD-016
related_sops:
  - SOP-025
  - SOP-029
related_systems:
  - SYSTEM-015
example: true
---

## Purpose

The SKU lifecycle management process governs the creation, maintenance, and retirement of Stock Keeping Unit records throughout their active life in the inventory platform. Consistent lifecycle management prevents orphaned records, maintains data quality, and ensures that system behavior for active, discontinued, and archived SKUs is predictable and well-defined.

## Scope

- All SKU records from initial creation request through final archival
- SKU status transitions: `draft` → `active` → `discontinued` → `archived`
- Variant creation, attribute updates, and category reassignments for existing SKUs
- Does not cover pricing or commercial terms, which are managed by the product catalog system

## Roles and Responsibilities

- **Product Manager**: Initiates SKU creation and discontinuation requests; owns the business case for each lifecycle decision
- **Inventory Platform Engineer**: Implements status transitions and validates data integrity during lifecycle changes
- **Warehouse Operations Lead**: Confirms physical stock disposition before a SKU is moved to discontinued or archived status
- **Data Analyst**: Monitors SKU activity metrics and flags candidates for discontinuation review
- **Compliance Officer**: Reviews archival decisions for SKUs with associated regulatory obligations

## Triggers

- New product addition request from the product team
- Product discontinuation decision from commercial leadership
- Automated dead stock detection flag (180 days zero movement per the Dead Stock Disposal Policy)
- Annual SKU portfolio review generating a list of candidates for status change

## Inputs

- SKU creation form with all required attributes per the SKU Naming Convention Standard
- Discontinuation approval from product management and commercial leadership
- Current on-hand quantity and pending orders report for any SKU being discontinued

## Outputs

- New SKU record in `active` status with all required fields populated
- Updated SKU status record with transition timestamp and approver identity
- Disposition plan for on-hand stock of discontinued SKUs
- Archived SKU record retained per the Warehouse Data Retention Policy

## Steps

1. Receive SKU creation or lifecycle change request and verify that the request includes all required approvals for the requested transition
2. For new SKUs: validate proposed SKU identifier against the naming convention standard and check for duplicates in the SKU registry
3. Create or update the SKU record in the inventory platform via the SKU management API, setting the appropriate status
4. For discontinuations: generate a current stock and open orders report for the SKU; ensure no open purchase orders reference the SKU before proceeding
5. Warehouse Operations Lead confirms the disposition plan for on-hand discontinued stock (liquidation, return to supplier, or disposal per the Dead Stock Disposal Policy)
6. Update SKU status to `discontinued`; the system automatically suppresses the SKU from replenishment signals and new order allocation
7. Once on-hand quantity reaches zero and the retention period for movement logs is satisfied, submit the archival request
8. Move SKU to `archived` status; archived SKUs are removed from active API responses but retained in the audit log

## Controls

- SKU status transitions must be performed via the API; direct database status updates are prohibited
- Discontinuation of a SKU with on-hand quantity greater than zero requires Warehouse Operations Lead confirmation
- SKU identifiers must not be reused for 5 years after archival
- All status transitions are logged with actor identity and timestamp in the stock movement log
