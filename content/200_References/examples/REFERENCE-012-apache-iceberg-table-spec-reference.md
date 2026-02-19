---
id: REFERENCE-012
type: reference
title: Apache Iceberg Table Spec Reference
status: draft
owner: Engineering Team
created: '2025-11-13T10:28:21.603Z'
updated: '2025-04-26T21:06:36.170Z'
tags:
  - reference
  - data-pipeline
summary: Apache Iceberg Table Spec Reference
upstream_url: https://docs.example.com/apache-iceberg-table-spec-reference
last_synced: '2026-10-03T00:43:22.611Z'
attribution: IEEE
license: CC BY-SA 4.0
category: standard
example: true
---

## Overview

Apache Iceberg is an open table format for large analytic datasets. It provides ACID transactions, schema evolution, partition evolution, time travel, and hidden partitioning on top of object storage (S3, GCS, ADLS). This reference summarizes the Iceberg v2 table specification features most relevant to our data lake implementation.

The data platform uses Iceberg v2 for all layers of the data lake (raw, transformed, and serving). For our specific configuration decisions, see ADR-0023.

## Table Format Concepts

### Snapshots and Snapshot History

An Iceberg table's state is represented by a series of immutable **snapshots**. Each write operation (append, overwrite, delete) creates a new snapshot that references a set of data files. The current table state is the most recent snapshot.

- **Snapshot**: A point-in-time table state. Contains references to all data files valid at that point.
- **Snapshot log**: The ordered history of all snapshots for a table.
- **Time travel**: Query a table AS OF a past snapshot ID or timestamp.

```sql
-- Query the table as of a specific snapshot
SELECT * FROM orders WHERE system_version(1234567890)

-- Query the table as of a timestamp
SELECT * FROM orders FOR TIMESTAMP AS OF TIMESTAMP '2025-01-01 00:00:00'
```

Snapshot expiry removes old snapshots and their orphaned data files. We run snapshot expiry on a 7-day retention window for the raw layer and 90-day retention for the marts layer.

### Manifest Files and Manifest Lists

Iceberg uses a three-level metadata tree:

1. **Table metadata file** (`metadata.json`): References the current manifest list and schema/partition spec
2. **Manifest list** (`snap-{snapshot-id}-{attempt}.avro`): Lists all manifest files for a snapshot
3. **Manifest file** (`{uuid}.avro`): Lists the data files in a partition, with partition statistics and column statistics (min/max, null count)

This structure enables **predicate pushdown** at the manifest level: Iceberg prunes manifest files that cannot contain rows matching the query predicate, without opening any data files.

### Hidden Partitioning

Iceberg supports **transform-based partitioning** where the partition value is derived from a column value rather than stored explicitly:

| Transform | Column Type | Example Partition | Use Case |
|-----------|-------------|-------------------|----------|
| `identity` | Any | `region=us-east-1` | Low-cardinality string dimensions |
| `days(ts)` | Timestamp | `event_date=2025-03-15` | Daily partitions |
| `hours(ts)` | Timestamp | `event_hour=2025-03-15-14` | Hourly partitions |
| `bucket(n, col)` | Any | `id_bucket=42` | High-cardinality ID ranges |
| `truncate(n, col)` | String/Int | `zip_prefix=94` | Prefix-based partitions |

**Our configuration**: Raw and staging layers partition by `days(event_time)`. Mart tables partition by `days(report_date)`. The transform is invisible to query writers — predicates on `event_time` are automatically translated to partition filter.

### Schema Evolution

Iceberg v2 supports the following schema changes without rewriting data files:

| Change | Allowed? | Notes |
|--------|----------|-------|
| Add a column | Yes | New column reads as null in existing files |
| Drop a column | Yes | Column is removed from schema; existing files retain the bytes but they are not read |
| Rename a column | Yes | Schema tracks column ID separately from name |
| Reorder columns | Yes | Physical order in Parquet is separate from schema order |
| Widen a type | Yes | `int` → `long`, `float` → `double`, `decimal(P,S)` → `decimal(P2,S)` where P2>P |
| Narrow a type | No | Cannot reduce precision |
| Change type incompatibly | No | `string` → `int` is not allowed |

**Producer discipline required**: Avro schema compatibility enforcement in the Schema Registry prevents incompatible type changes from reaching Iceberg. The Schema Registry's BACKWARD compatibility mode ensures that Iceberg schema evolution rules are not violated.

### Merge-on-Read vs. Copy-on-Write

Iceberg v2 supports two merge modes for UPDATE/DELETE/MERGE DML operations:

**Copy-on-Write (CoW)**:
- On UPDATE/DELETE: rewrites entire data files containing affected rows
- Produces clean data files; reads are fast
- Writes are expensive for sparse updates
- **Our usage**: All ingestion writes use CoW; ingestion is append-only, so CoW cost is not incurred

**Merge-on-Read (MoR)**:
- On UPDATE/DELETE: writes a delete file recording row-level deletions; original data files unchanged
- Writes are fast; reads must merge delete files with data files
- Requires periodic compaction to collapse delete files into clean data files
- **Our usage**: dbt `MERGE INTO` statements for incremental mart models use MoR by default in Trino

### Compaction

Over time, frequent small writes create many small data files, degrading read performance. Iceberg compaction rewrites small files into larger, optimized files within the same partition:

```sql
-- Trino compaction (bin-pack strategy, target file size 128 MB)
ALTER TABLE orders EXECUTE optimize WHERE event_date >= DATE '2025-03-01'
```

**Our compaction schedule**:
- Raw layer: Daily at 02:00 UTC, targeting 128 MB files
- Staging layer: Daily at 03:00 UTC
- Marts layer: Weekly on Sunday at 04:00 UTC (lower write frequency)

## File Format Details

Iceberg supports three data file formats. We use **Parquet** exclusively:

- **Parquet**: Column-oriented, excellent compression, supports predicate pushdown via column statistics and bloom filters. Default for analytics workloads.
- **ORC**: Column-oriented; strong in Hive ecosystem; we do not use ORC.
- **Avro**: Row-oriented; used only for Iceberg metadata files (manifest files are always Avro regardless of data file format).

**Our Parquet configuration**:
- Compression: Snappy (balance of speed and ratio)
- Row group size: 128 MB
- Page size: 1 MB
- Dictionary encoding: enabled for low-cardinality string columns

## Sync Notes

This reference summarizes the Apache Iceberg v2 table specification features most relevant to our data lake. For the full specification, see the upstream URL (Apache Iceberg official documentation). Re-sync when the platform upgrades to a new Iceberg spec version or when new features are adopted.
