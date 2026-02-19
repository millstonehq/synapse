---
id: GUIDE-032
type: guide
title: Writing Idempotent Data Transforms
status: accepted
owner: Developer Experience
created: '2024-12-05T17:39:12.620Z'
updated: '2026-09-18T21:05:41.674Z'
tags:
  - guide
  - data-pipeline
summary: Writing Idempotent Data Transforms
audience: internal
related_systems:
  - SYSTEM-027
  - SYSTEM-029
related_sops:
  - SOP-056
  - SOP-052
example: true
---

## Why Idempotency Matters

A data transform that is not idempotent will produce duplicate records, incorrect aggregations, or inconsistent state every time it is re-run after a failure. Because pipelines fail — due to transient infrastructure errors, upstream data gaps, or deployment rollbacks — every transform must be written to handle re-execution gracefully. An idempotent transform run twice produces the same output as running it once.

## The Core Pattern: Overwrite, Don't Append

The most reliable way to achieve idempotency in batch transforms is the **overwrite partition** pattern:

1. Compute all output records for a specific time partition (e.g., `dt=2024-11-15`)
2. Delete the existing data for that partition in the target table
3. Write the new computed records to the partition

This guarantees that no matter how many times the job runs for a given partition, the output contains exactly the correct records for that execution date. In Spark, use `insertInto` with `overwrite=True` or a `REPLACE WHERE dt = '...'` DML statement. In dbt, use an incremental model with `unique_key` and `merge` strategy.

## Avoiding Common Anti-Patterns

Several common transform patterns break idempotency:

- **Append-only writes without deduplication**: Each re-run adds duplicate records. Fix by using `MERGE INTO` or partition overwrite instead of `INSERT INTO`.
- **Side effects in transformation logic**: Writing to an external API or sending notifications during a transform step means re-runs trigger duplicate external actions. Move side effects outside the transform, gated by a status check.
- **Using `NOW()` or `CURRENT_TIMESTAMP` as a data field**: This causes different results on every run. Use the pipeline's logical execution date instead.
- **Accumulating state without resetting**: Transforms that `SUM` into an existing total without first clearing the partition will double-count on re-run.

## Testing for Idempotency

Every transform should include an idempotency test in the test suite:

```python
# Run the transform twice for the same execution date
run_transform(execution_date="2024-11-15")
result_1 = query_target_partition("2024-11-15")
run_transform(execution_date="2024-11-15")
result_2 = query_target_partition("2024-11-15")
assert result_1.count() == result_2.count()
assert result_1.checksum() == result_2.checksum()
```

This test catches any append, accumulation, or timestamp-dependency issues before they reach production.

## Idempotency in Streaming Pipelines

For Kafka consumer processors, idempotency requires deduplication logic using a unique event ID or message offset:

- Store a processed event ID in a deduplication cache or database
- Before processing each message, check whether the event ID has already been handled
- Use exactly-once semantics in the Kafka consumer configuration where the broker version supports it

Consumer lag and rebalances will cause message redelivery; only deduplication logic prevents duplicate processing.

## Next Steps

- Review the Data Pipeline Idempotency Standard for the organization's specific requirements and controls
- Check the dbt project documentation for examples of correctly configured incremental models with `unique_key`
- Add an idempotency test to every new transform as part of the PR checklist
