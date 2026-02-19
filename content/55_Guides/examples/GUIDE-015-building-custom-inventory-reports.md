---
id: GUIDE-015
type: guide
title: Building Custom Inventory Reports
status: deprecated
owner: Engineering Team
created: '2024-10-08T14:24:18.291Z'
updated: '2025-04-22T01:26:34.148Z'
tags:
  - guide
  - inventory-management
summary: Building Custom Inventory Reports
audience: customer
related_systems:
  - SYSTEM-014
  - SYSTEM-013
related_sops:
  - SOP-022
  - SOP-026
example: true
---

## Why Custom Reports Matter

The standard inventory dashboards cover the most common operational metrics, but every warehouse operation has unique reporting needs — whether that's tracking slow-moving SKUs by supplier, monitoring stock levels across specific warehouse zones, or building a daily replenishment digest for your operations team. This guide shows you how to build custom reports against the inventory data platform.

## Available Data Sources

The inventory platform exposes three data access paths for reporting:

**Inventory REST API** — best for real-time point-in-time queries on specific SKUs or warehouses. Use this for reports that need fresh data and operate on a small set of records. The API enforces pagination limits of 1,000 records per request, so it is not suitable for large bulk exports.

**ClickHouse Analytics Database** — best for historical trend analysis, aggregations across all warehouses, and bulk data exports. The analytics database is updated every 5 minutes from the primary inventory store. Use the read-only analytics credentials (contact the Inventory Platform team). Example connection: `clickhouse://analytics-ro@clickhouse.internal:9000/inventory`.

**Reconciliation Report Archive** — nightly reconciliation reports are exported to the S3 bucket `s3://inventory-reports/reconciliation/`. These are CSV files suitable for import into spreadsheet tools or BI platforms.

## Building a Report in ClickHouse

Connect to the analytics ClickHouse instance using your preferred SQL client. The key tables are:

- `inventory.stock_snapshots` — daily stock level snapshots per SKU per warehouse
- `inventory.stock_movements` — full movement log with type, quantity, and actor
- `inventory.skus` — SKU master data including category, supplier, and status

Example: total movement volume by movement type for the past 30 days:

```sql
SELECT
    movement_type,
    count() AS event_count,
    sum(abs(quantity_delta)) AS total_units_moved
FROM inventory.stock_movements
WHERE occurred_at >= now() - INTERVAL 30 DAY
GROUP BY movement_type
ORDER BY total_units_moved DESC
```

## Scheduling and Distributing Reports

For recurring reports, use the internal Report Scheduler (accessible via the Inventory Admin Portal under Reports > Scheduled). You can configure SQL queries to run on a cron schedule and deliver results to an email list or a Slack channel. Reports are stored in the reconciliation archive for 90 days.

For one-off large exports (more than 500,000 rows), use the bulk export job endpoint rather than running a direct ClickHouse query to avoid impacting the analytics cluster:

```bash
curl -X POST https://inventory-api.internal/v1/reports/export \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query_type": "stock_movements", "date_from": "2025-01-01", "warehouse_id": "WH001"}'
```

The API returns a job ID; poll the job status endpoint until the export file is available in S3.

## Common Pitfalls

- **Avoid querying `stock_snapshots` for real-time availability** — snapshots are up to 5 minutes old. Use the REST API for real-time availability checks.
- **Always filter by date range in movement log queries** — the movements table is large. Unfiltered queries will time out.
- **Use the analytics read-only credentials** — never use application credentials for reporting queries. Direct database access from reporting tools can cause connection pool pressure on the application database.
