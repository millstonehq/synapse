---
id: GUIDE-063
type: guide
title: Inventory Batch Import Guide
status: accepted
owner: Engineering Team
created: '2024-09-10T23:06:55.010Z'
updated: '2025-01-07T09:34:54.331Z'
tags:
  - guide
  - inventory-management
summary: Inventory Batch Import Guide
audience: internal
related_systems:
  - SYSTEM-011
  - SYSTEM-013
related_sops:
  - SOP-023
  - SOP-029
example: true
---

## Why Batch Import Exists

The inventory platform is event-sourced: every stock change flows through the Inventory Event Bus as an immutable `StockReceived`, `StockAdjusted`, or `StockTransferred` event. For day-to-day operations this works well — individual warehouse movements arrive as real-time events via the warehouse integration adapters.

But there are situations where you need to load a large number of stock records at once:

- **Initial onboarding**: A new merchant joins the platform and needs their existing stock loaded from a spreadsheet or WMS export
- **Bulk corrections**: After a reconciliation exercise, hundreds of SKUs need their system quantities aligned with physical counts
- **Migration**: Moving stock data from a legacy system to the new platform
- **Seasonal restocking**: A merchant receives a large delivery and their WMS cannot send individual events fast enough

The batch import pipeline ([[SYSTEM-011|Inventory Tracking Service]] processes the output; [[SYSTEM-013|Stock Level Calculator]] picks up the resulting events) is designed to handle these situations efficiently without overwhelming the event bus or causing stock level inconsistencies.

## The Mental Model

Think of a batch import as a controlled flood of synthetic stock events. The batch pipeline:

1. Validates your input file (format, required fields, SKU resolution)
2. Converts each row into one or more stock events
3. Publishes those events to the Inventory Event Bus with a special `source=BATCH_IMPORT` tag
4. The Stock Level Calculator processes the events and updates stock projections

The `source=BATCH_IMPORT` tag is important: it tells the automated reorder evaluation engine to ignore these events when checking reorder thresholds, preventing a flood of purchase orders being triggered by the import. Once the import is complete and stock levels are stable, the reorder engine resumes normal evaluation.

For the exact commands and configuration, see [[SOP-023|Batch Import SOP]]. For ongoing reconciliation procedures, see [[SOP-029|Stock Reconciliation SOP]].

## Preparing Your Import File

### Supported Formats

The batch import pipeline accepts:

- **CSV**: Comma-separated values with a header row
- **JSON Lines (JSONL)**: One JSON object per line, no wrapping array
- **Excel (XLSX)**: First sheet only; header row required

### Required Fields

Every row must include:

| Field | Description | Example |
|-------|-------------|---------|
| `sku_id` or `gtin` | SKU identifier (internal ID or GTIN-13/14) | `SKU-00123` or `5901234123457` |
| `location_id` | Warehouse location identifier | `WH-001` |
| `qty` | Quantity to set or adjust | `250` |
| `import_type` | Whether this is a `SET` (absolute) or `ADJUST` (delta) | `SET` |

### Optional Fields

| Field | Description |
|-------|-------------|
| `batch_ref` | Lot or batch number (for expiry-tracked items) |
| `expiry_date` | Expiry date in ISO 8601 format (YYYY-MM-DD) |
| `cost_price` | Unit cost for COGS calculations |
| `notes` | Free-text note attached to the generated event |

### SET vs ADJUST

- **SET** (`import_type=SET`): The pipeline generates a `StockAdjusted` event that brings the current system quantity to exactly the value in the `qty` field. Use this when you are loading an absolute stock count (e.g., from a WMS snapshot). The pipeline reads the current system quantity, calculates the delta, and publishes the adjustment. If current quantity is 100 and you SET to 150, the event delta will be +50.

- **ADJUST** (`import_type=ADJUST`): The pipeline generates a `StockReceived` (positive delta) or `StockAdjusted` (negative delta) event with the exact value in the `qty` field as the delta. Use this when you have a list of movements to apply (e.g., a batch of receipts that were not processed in real time).

### Common Mistakes to Avoid

- **Uploading a full stock snapshot as ADJUST**: This doubles the stock for every SKU. Always use SET for absolute quantities.
- **Including inactive SKUs**: The pipeline rejects rows where the SKU is not active in the SKU Registry. Check for inactive SKUs before uploading.
- **Missing location IDs**: Rows with an unrecognised `location_id` are rejected and written to the error report. Verify all warehouse IDs against the location registry before uploading.
- **Mixing GTIN and sku_id without checking for duplicates**: If the same SKU appears both by `sku_id` and by `gtin`, it will be imported twice. Deduplicate your file before uploading.

## Running the Import

### Step 1: Validate the File

Before submitting a batch import, run the validation command to check your file for errors without publishing any events:

```bash
inv-batch-import validate \
  --file /path/to/import.csv \
  --merchant-id MERCHANT-123 \
  --dry-run
```

The validator outputs:
- Total rows
- Rows with validation errors (with row numbers and error descriptions)
- SKUs that could not be resolved
- Locations that are not registered

Fix all errors before proceeding. A file with any errors will be rejected at submission time.

### Step 2: Submit the Import

```bash
inv-batch-import submit \
  --file /path/to/import.csv \
  --merchant-id MERCHANT-123 \
  --import-reason "Initial onboarding from WMS export 2025-01-07"
```

The import is queued and you receive a job ID. Large imports (> 50,000 rows) are processed asynchronously. You will receive an email notification when the job completes or if it encounters errors.

### Step 3: Monitor Progress

```bash
inv-batch-import status --job-id IMPORT-JOB-456
```

The status output shows:
- Rows processed / total rows
- Events published successfully
- Rows skipped or failed (with reasons)
- Estimated completion time for large jobs

### Step 4: Review the Import Report

After completion, download the import report to review any skipped rows:

```bash
inv-batch-import report --job-id IMPORT-JOB-456 --output /tmp/report.csv
```

Review the report for skipped or failed rows and determine whether they need to be re-processed or whether the skips are expected (e.g., rows for discontinued SKUs).

## Large Import Performance Guidelines

| Row Count | Expected Duration | Notes |
|-----------|-------------------|-------|
| < 1,000 | < 30 seconds | Synchronous processing |
| 1,000 - 50,000 | 1-15 minutes | Asynchronous; email on completion |
| 50,000 - 500,000 | 15-90 minutes | Off-peak window recommended |
| > 500,000 | Contact platform team | Requires pre-coordination for event bus capacity |

For imports over 50,000 rows, schedule the import during off-peak hours (22:00-06:00 UTC) to avoid contention with real-time warehouse event processing.

## Next Steps

- Review the [[SOP-023|Batch Import SOP]] for the full operational procedure including approval workflows for large imports
- For post-import reconciliation, see the [[SOP-029|Stock Reconciliation SOP]]
- If you encounter unexpected stock levels after an import, check the import event log for the affected SKUs using the `source=BATCH_IMPORT` filter on the stock movement history
