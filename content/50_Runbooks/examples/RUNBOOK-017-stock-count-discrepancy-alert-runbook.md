---
id: RUNBOOK-017
type: runbook
title: Stock Count Discrepancy Alert Runbook
status: approved
owner: On-Call Engineer
created: '2025-03-19T20:17:53.462Z'
updated: '2026-09-26T07:20:44.135Z'
tags:
  - runbook
  - inventory-management
summary: Stock Count Discrepancy Alert Runbook
example: true
---

## Service

- **System**: [[SYSTEM-011|Inventory Tracking Service]]
- **Owner team**: Inventory Engineering
- **On-call rotation**: PagerDuty schedule "inventory-oncall"
- **Slack channel**: #inventory-incidents
- **Runtime**: Kubernetes / Go 1.22 / ClickHouse / Kafka

## Alerts

- `stock_discrepancy_threshold_exceeded` - System vs. physical count variance exceeds 0.5% by value for a SKU after a cycle count reconciliation
- `stock_negative_quantity_detected` - A SKU's `on_hand_qty` has dropped below zero in the inventory database
- `stock_discrepancy_open_48h` - A flagged discrepancy has not been resolved within 48 hours (policy breach)
- `stock_audit_reconciliation_failed` - The post-audit reconciliation report generated a diff that could not be automatically categorized

## Diagnosis Steps

1. **Identify the scope of the discrepancy** - Query the inventory API for the flagged SKU and warehouse. Note the system quantity, the reported physical quantity, the discrepancy magnitude, and the timestamp of the last system update.
2. **Check recent stock movement events** - Pull the movement log for the SKU for the past 72 hours. Look for any unusual patterns: duplicate entries, large adjustments without a reference order, or a gap in movement records that could indicate missed sync events.
3. **Check for recent sync errors for this warehouse** - Review the sync service error log for the warehouse associated with the discrepancy. A sync failure in the relevant window could explain missing movement records.
4. **Determine if this is an isolated SKU or systemic** - Query the discrepancy monitoring dashboard to see if multiple SKUs in the same warehouse are flagged. A systemic discrepancy pattern points to a sync or integration problem rather than a counting error.
5. **Contact the Warehouse Operations Lead** - If the discrepancy cannot be explained by system logs, request a manual spot count for the affected SKU to establish the true physical quantity.

## Remediation Steps

1. **If caused by a missed sync event** - Identify the missing event in the WMS audit log and manually re-inject it via the inventory event replay endpoint. Verify the quantity corrects as expected.
2. **If caused by a duplicate movement record** - Identify the duplicate `movement_id` in the movement log. Contact the Inventory Platform Engineer to apply a corrective adjustment to reverse the duplicate, referencing the original and duplicate movement IDs.
3. **If the physical count confirms a true discrepancy** - Follow the Investigate Stock Mismatch SOP to gather evidence, obtain approval, and apply a corrective adjustment.
4. **If `on_hand_qty` is negative** - This is a system integrity failure requiring immediate attention. Do not apply an adjustment without first determining why the quantity went negative. Escalate to the Inventory Platform Engineer immediately.
5. **If the discrepancy is systemic across a warehouse** - Disable automated order allocation for the affected warehouse pending a full audit. Notify the Warehouse Operations Lead and escalate to Engineering Manager.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks discrepancy scope |
| 15 min | Post findings in #inventory-incidents; contact Warehouse Operations Lead if physical count is needed |
| 30 min | If negative quantity detected: immediately escalate to Inventory Platform Engineer |
| 48 h | Unresolved discrepancy must be escalated to Director of Engineering per policy |

## Dashboards

- [Inventory Discrepancy Monitor](https://grafana.example.com/d/inventory-discrepancy) - Open discrepancies by SKU, warehouse, and magnitude
- [Stock Movement Log](https://grafana.example.com/d/inventory-movements) - Recent movements with event source and actor
- [Inventory Sync Overview](https://grafana.example.com/d/inventory-sync) - Sync health and error rates by warehouse
- [Inventory Data Quality](https://grafana.example.com/d/inventory-dq) - Negative quantity counts, stale records, validation failures
