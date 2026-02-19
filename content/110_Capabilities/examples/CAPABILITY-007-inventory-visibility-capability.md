---
id: CAPABILITY-007
type: capability
title: Inventory Visibility Capability
status: approved
owner: VP Engineering
created: '2024-03-05T04:31:40.086Z'
updated: '2026-07-14T08:26:25.159Z'
tags:
  - capability
  - inventory-management
summary: Inventory Visibility Capability
evidence_links:
  - PROCESS-013
  - POLICY-013
  - PROCESS-018
example: true
---

## Domain

- Inventory Management
- Operations
- Merchant Experience

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No real-time stock visibility. Merchants rely on nightly batch reports that are out of date by morning. Stock positions are unknown until a stockout occurs.
- **Level 1 - Ad hoc**: Some stock queries are possible via direct database access for specific merchants, but there is no standardised interface. Freshness and accuracy are inconsistent.
- **Level 2 - Repeatable**: A per-location inventory dashboard exists. Merchants can view stock for individual warehouses but must switch views to aggregate across locations. Stock data is delayed by up to 5 minutes.
- **Level 3 - Defined** (current): Real-time dashboard with < 10-second refresh, multi-warehouse aggregated view, movement history, and configurable low-stock alerts. Data is sourced from the Stock Level Calculator event projection. Operations teams have cross-merchant visibility for support.
- **Level 4 - Managed**: Proactive alerting when stock approaches reorder points, with SLO-tracked freshness metrics and automated reconciliation when system and warehouse quantities diverge.
- **Level 5 - Optimizing**: Predictive visibility with demand-driven stockout probability scoring; automated suggested actions surfaced to merchants before problems occur.

**Gap to Level 4**: Proactive low-stock alerts are in progress. Automated reconciliation tooling is not yet built. Freshness SLO dashboards need to be published to the merchant-facing status page.

## Metrics

- Stock data freshness (P95): Currently 8s from movement event to dashboard, target < 10s
- Multi-warehouse aggregation query latency (P95): Currently 420ms, target < 500ms
- Merchant adoption: 62% of active merchants view the dashboard weekly, target 70%
- Reconciliation discrepancy rate: 0.3% of SKUs have a system-vs-warehouse quantity mismatch on any given day, target < 0.1%
- Support tickets for stock level inquiries: Down 45% since dashboard launch, target 60% reduction

## Evidence Links

- [[PROCESS-013|Inventory Reconciliation Process]] - Process for detecting and resolving system vs warehouse quantity discrepancies
- [[POLICY-013|Inventory Data Accuracy Policy]] - Policy mandating freshness and accuracy standards for stock data
- [[PROCESS-018|Warehouse Sync Monitoring Process]] - Process for monitoring warehouse connection health and detecting stale sync feeds

## Notes

The capability advanced from Level 2 to Level 3 in Q2 2025 with the launch of the real-time dashboard and multi-warehouse aggregated view. The key architectural enabler was the event-sourced Stock Level Calculator that computes stock positions from an immutable event log rather than mutable in-place updates.

Key improvements needed for Level 4:
- Implement proactive low-stock alerts with merchant-configurable thresholds that trigger notifications rather than requiring merchants to check the dashboard
- Build automated reconciliation: schedule periodic comparison of system stock quantities against WMS snapshots and auto-create adjustment events for confirmed discrepancies
- Publish freshness SLO dashboards to the merchant portal so merchants can see data staleness directly
