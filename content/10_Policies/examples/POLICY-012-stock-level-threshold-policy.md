---
id: POLICY-012
type: policy
title: Stock Level Threshold Policy
status: draft
owner: CTO
created: '2024-08-17T10:27:21.459Z'
updated: '2025-12-01T21:24:31.407Z'
tags:
  - policy
  - inventory-management
summary: Stock Level Threshold Policy
example: true
related_standards:
  - STANDARD-013
  - STANDARD-014
---

## Scope

This policy governs how minimum stock level thresholds are defined, maintained, and acted upon across all warehouses and product categories. It applies to inventory planners, warehouse managers, engineering systems that evaluate stock levels, and any automated replenishment or alerting logic within the inventory platform.

## Rationale

- Stockouts result in lost sales, degraded customer experience, and potential SLA violations with enterprise customers
- Overstocking ties up working capital, increases warehousing costs, and accelerates the risk of dead stock accumulation
- Consistent threshold definitions prevent conflicting replenishment signals across warehouse regions and product lines
- Automated threshold enforcement reduces reliance on manual monitoring and shortens response time to low-stock conditions

## Policy Statements

- Every active SKU must have a defined minimum stock threshold and a reorder point configured in the inventory system
- Thresholds must be reviewed and updated at minimum quarterly, or immediately following a significant demand event
- When on-hand quantity falls to or below the reorder point, an automated replenishment signal must be generated within one hour
- Critical SKUs (defined as those generating more than 5% of monthly revenue) must maintain a safety stock buffer of at least 10% above the minimum threshold
- Stock level thresholds must not be modified by automated systems without a logged approval from an authorized inventory planner
- Threshold violations unresolved for more than 72 hours must be escalated to the inventory operations lead

## Related Standards

- [[STANDARD-013|Inventory API Schema Standard]]
- [[STANDARD-014|SKU Naming Convention Standard]]
