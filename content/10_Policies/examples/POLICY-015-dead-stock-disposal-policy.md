---
id: POLICY-015
type: policy
title: Dead Stock Disposal Policy
status: proposed
owner: CTO
created: '2025-04-01T04:11:02.587Z'
updated: '2026-06-28T08:20:42.424Z'
tags:
  - policy
  - inventory-management
summary: Dead Stock Disposal Policy
example: true
related_standards:
  - STANDARD-015
  - STANDARD-013
---

## Scope

This policy applies to all SKUs classified as dead stock — defined as items with zero sales movement for 180 consecutive days and no pending purchase orders. It covers the identification, approval, and disposal workflows for dead stock across all warehouse locations, including returns processing centers and third-party logistics partners.

## Rationale

- Dead stock consumes warehouse space that could be allocated to higher-velocity items, increasing per-unit storage costs
- Carrying dead stock inflates inventory asset values on the balance sheet, creating financial reporting inaccuracies
- Timely disposal reduces the risk of product obsolescence, expiry, or damage that could make items unsaleable
- Standardized disposal procedures prevent unauthorized write-offs and ensure appropriate accounting treatment

## Policy Statements

- SKUs meeting the dead stock definition must be flagged automatically by the inventory system and presented for review within 7 days
- Disposal decisions must be approved by both the inventory operations lead and the relevant category manager before any action is taken
- Approved disposal methods in order of preference are: liquidation sale, donation to approved charity partners, recycling through certified partners, destruction
- All disposed inventory must be recorded in the inventory system with disposal method, date, quantity, and approver identity before physical removal
- Write-off values exceeding $10,000 require additional finance team approval
- Dead stock disposal records must be retained in accordance with the Warehouse Data Retention Policy

## Related Standards

- [[STANDARD-015|Warehouse Event Format Standard]]
- [[STANDARD-013|Inventory API Schema Standard]]
