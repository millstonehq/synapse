---
id: ADR-0023
type: adr
title: Use Apache Iceberg for Data Lake Format
status: deprecated
owner: Tech Lead
created: '2025-07-30T03:13:26.708Z'
updated: '2025-10-06T11:05:33.005Z'
tags:
  - adr
  - data-pipeline
summary: Use Apache Iceberg for Data Lake Format
example: true
---

## Context

The data platform stores raw and transformed data across multiple source systems (orders, inventory, user events, payments). As data volumes grow toward 50 TB, the team evaluated open table formats for the data lake layer. Key requirements:

- **ACID transactions**: Concurrent writes from multiple ECS ingestion tasks must not corrupt table state
- **Schema evolution**: Source system schemas change frequently; the data lake must absorb additions and renames without rewriting history
- **Time travel**: Compliance and audit workflows require point-in-time reads going back at least 90 days
- **Partition evolution**: Initial partitioning by ingestion date must be changeable to event date without full table rewrites
- **Compute engine compatibility**: Tables must be readable by Trino, Spark, and dbt without format conversion

The team evaluated Apache Iceberg, Apache Hudi, and Delta Lake. Storage backend is S3.

## Decision

Adopt **Apache Iceberg** as the table format for all data lake layers (raw, transformed, and serving).

All new Iceberg tables will use the v2 spec. Partition spec: partition by `event_date` using the `days` transform. Metadata location: `s3://data-lake-prod/{layer}/{table_name}/metadata/`. The Data Lake Ingestion Service will write using the Iceberg Java SDK with S3FileIO. dbt reads tables via the dbt-trino adapter. All DDL is managed through the infrastructure-as-code repository using Terraform with the Iceberg Trino catalog.

## Consequences

**Positive:**
- Hidden partitioning decouples physical layout from query predicates, preventing partition pruning errors for consumers
- Copy-on-write merge mode provides strong ACID guarantees needed for concurrent ECS task writes
- Time travel queries via `AS OF` syntax satisfy 90-day audit and compliance read requirements
- Schema evolution (add/rename/reorder columns) without rewriting existing data files
- Broad engine support: Trino, Spark, dbt-trino, and AWS Athena all read Iceberg v2 natively

**Negative:**
- Iceberg metadata files accumulate over time; a compaction and snapshot expiry job must be run periodically
- Small file problem with streaming writes — merge-on-read mode reduces write amplification but requires periodic compaction to maintain read performance
- Operational complexity higher than plain Parquet/Hive tables; engineers must understand snapshot lifecycle management

**Neutral:**
- Catalog choice (Glue vs. Hive Metastore vs. REST) is decoupled from table format and can be changed independently
- Migration of existing Hive-format tables to Iceberg will be staged over Q2–Q3 2025

## Alternatives Considered

**Apache Hudi:**
- Pro: Mature streaming upsert support (MOR tables), strong CDC ingestion story, built-in Hive sync
- Con: Complexity of MOR vs. COW mode selection per table; dbt integration less mature than Iceberg; timeline metadata introduces Hive Metastore dependency
- Rejected because: dbt-trino + Iceberg integration was more mature and better documented for our transformation workload pattern

**Delta Lake:**
- Pro: Deep Spark integration, strong DML support, extensive community
- Con: Delta's open-source catalog support lagged behind Iceberg at evaluation time; Trino's Delta connector was read-only at the time of evaluation; vendor alignment with Databricks creates lock-in concerns
- Rejected because: Read-only Trino connector would prevent our Trino-based transformation tier from writing Delta tables

**Plain Parquet with Hive partitioning:**
- Pro: No additional framework, maximum compatibility, simple tooling
- Con: No ACID guarantees (concurrent writes risk corruption), no schema evolution without manual DDL, no time travel, partition changes require full table rewrites
- Rejected because: ACID and time travel requirements cannot be met without a table format layer
