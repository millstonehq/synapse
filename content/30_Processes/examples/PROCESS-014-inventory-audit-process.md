---
id: PROCESS-014
type: process
title: Inventory Audit Process
status: review
owner: Director of Engineering
created: '2025-02-01T00:44:43.368Z'
updated: '2026-01-15T21:27:21.710Z'
tags:
  - process
  - inventory-management
summary: Inventory Audit Process
related_standards:
  - STANDARD-016
  - STANDARD-013
related_sops:
  - SOP-021
  - SOP-029
related_systems:
  - SYSTEM-015
example: true
---

## Purpose

The inventory audit process establishes how physical stock counts are compared against system records to identify and resolve discrepancies. Regular audits maintain inventory data accuracy, satisfy financial reporting requirements, and provide the evidence base needed to investigate and prevent systematic counting or syncing errors.

## Scope

- Scheduled cycle counts covering all active warehouses on a rotating basis
- Full physical inventory audits conducted annually or triggered by a significant discrepancy event
- Spot audits initiated by the finance team, external auditors, or following a reported incident
- Does not cover virtual inventory adjustments; those are handled by the Investigate Stock Mismatch SOP

## Roles and Responsibilities

- **Audit Coordinator**: Schedules audit windows, assigns warehouse teams, and tracks completion status
- **Warehouse Count Team**: Conducts the physical count and submits count sheets for all assigned locations
- **Inventory Data Analyst**: Pulls system snapshot reports, performs discrepancy analysis, and produces the audit reconciliation report
- **Inventory Operations Lead**: Reviews discrepancy findings, approves adjustments, and signs off on audit completion
- **Finance Representative**: Reviews audit results for financial reporting purposes and flags any material discrepancies

## Triggers

- Scheduled cycle count calendar event (weekly zone rotation across warehouses)
- Annual full physical inventory audit (fiscal year-end)
- Discrepancy alert where system vs. physical variance exceeds 1% by value for any SKU
- External audit requirement from finance or regulatory body

## Inputs

- Warehouse zone assignment map for the audit period
- System inventory snapshot exported at audit start time (frozen reference)
- Blank count sheets or mobile count application configured for the audit session
- Previous audit results for trend comparison

## Outputs

- Completed count sheets with physical quantities for all audited SKUs
- Reconciliation report comparing physical counts against system snapshot
- List of approved inventory adjustments to be applied in the system
- Audit completion sign-off and archive record

## Steps

1. Export a frozen inventory snapshot from the system for the warehouse zones being audited; record the snapshot timestamp
2. Distribute count sheets or configure mobile counting devices for the assigned warehouse team
3. Warehouse count team completes physical counts for all SKUs in assigned zones without reference to system quantities
4. Count team submits completed count sheets to the Inventory Data Analyst
5. Analyst imports count results and runs the discrepancy comparison against the frozen snapshot, flagging any variance above 0.5%
6. Investigate root causes for flagged discrepancies using stock movement logs; categorize each as: counting error, sync lag, system bug, or unknown
7. Inventory Operations Lead reviews findings and approves the correction list; adjustments above $5,000 value require Finance Representative co-approval
8. Apply approved inventory adjustments in the system via the standard adjustment API, referencing the audit ID in each adjustment record

## Controls

- Frozen snapshots must not be modified after export; the audit timestamp is the reference point for all comparisons
- Physical counters must be blinded to system quantities during the count to prevent confirmation bias
- All approved adjustments must reference the audit record ID for traceability
- Audit results and adjustment records must be retained per the Warehouse Data Retention Policy
