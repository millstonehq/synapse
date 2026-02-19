---
id: GUIDE-036
type: guide
title: Understanding the Data Lake Architecture
status: approved
owner: Engineering Team
created: '2024-07-14T14:00:30.445Z'
updated: '2025-12-17T07:38:16.608Z'
tags:
  - guide
  - data-pipeline
summary: Understanding the Data Lake Architecture
audience: internal
related_systems:
  - SYSTEM-028
  - SYSTEM-026
related_sops:
  - SOP-056
  - SOP-059
example: true
---

## Overview

The data lake is the central long-term storage layer for all raw and processed data at the organization. It is built on Amazon S3 and uses Apache Iceberg as the table format, providing ACID transactions, time travel, and efficient incremental reads without the lock-in of a traditional data warehouse. Understanding how the lake is structured is essential for building pipelines that read from and write to it correctly.

## The Zone Architecture

The data lake is organized into three zones, each with a distinct purpose and quality level:

**Raw zone** (`s3://data-lake/raw/`) contains unmodified data exactly as received from source systems. Data lands here from Kafka consumers, API connectors, and SFTP ingestion jobs. The raw zone is append-friendly but all downstream pipelines must treat raw data as potentially incomplete or duplicated.

**Cleaned zone** (`s3://data-lake/cleaned/`) contains deduplicated, schema-validated, and PII-masked versions of raw data. Pipelines that read from the cleaned zone can assume consistent schema and no duplicate events. All PII masking transformations happen in the raw-to-cleaned stage.

**Curated zone** (`s3://data-lake/curated/`) contains aggregated, joined, and business-domain-ready datasets. These are the datasets most analytics and ML consumers read from. Curated datasets are registered in the data catalog with full lineage and column-level documentation.

## File Format and Partitioning

All datasets in the cleaned and curated zones use Parquet format with Snappy compression. Iceberg manages the table metadata and partition evolution:

- Partition by `dt` (date string, `YYYY-MM-DD`) as the primary partition key for all time-series datasets
- Use Iceberg's hidden partitioning for datasets with high-cardinality secondary partition needs
- Target file sizes of 128MB–512MB per Parquet file to balance read performance and write overhead
- Run Iceberg compaction jobs weekly for high-write-frequency tables to merge small files

## Access Patterns

Data lake access is controlled via IAM roles assigned to pipeline service accounts:

- Pipeline service accounts get write access only to their own output prefix within the appropriate zone
- Analysts and ML engineers get read access to cleaned and curated zones via temporary credentials or Athena/Spark query federation
- No direct write access is granted to users for the cleaned or curated zones; all writes must go through pipeline service accounts
- PII-tagged datasets in the curated zone require an elevated access request approved by Data Governance

## Monitoring and Maintenance

Keeping the data lake healthy requires ongoing operational attention:

- Monitor storage growth per zone weekly; unusual growth in the raw zone often indicates a runaway ingestion pipeline
- Review Iceberg snapshot retention; expired snapshots free up storage but remove time travel capability — the default retention is 7 days
- Run the orphaned file cleanup job monthly to remove files that are not referenced by any Iceberg snapshot
- Check S3 lifecycle policies are executing correctly to transition infrequently-accessed data to cheaper storage tiers

## Next Steps

- Review the Data Retention and Archival Policy for the required retention periods per zone
- Familiarize yourself with the [[SOP-056|Rotate Kafka Cluster Certificates SOP]] and [[SOP-059|Update Schema Registry Entry SOP]] as they relate to data lake ingestion pipelines
- Use the data catalog to discover existing curated datasets before building a new pipeline that might duplicate existing work

## How Our Pipeline Works

### Build and Test

When you merge a PR to `main`, CI automatically:

- Runs the full test suite (unit, integration, E2E)
- Builds a Docker image tagged with the commit SHA
- Pushes the image to our container registry
- Generates a deployment manifest

You don't need to do anything here. If CI fails, the merge is blocked.

### The Change Ticket

Before deploying, you need an approved change ticket. This isn't bureaucracy - it's how we:

- Track what changed and why (audit trail)
- Ensure someone besides you reviewed the risk
- Coordinate timing so deploys don't collide

For low-risk changes (config updates, small bug fixes), approval is lightweight - your PR reviewer can approve the ticket. For high-risk changes (database migrations, new services, breaking API changes), you need a senior engineer's sign-off.

### The Deploy Itself

We use blue-green deployments. This means:

- The new version spins up alongside the old one
- Health checks verify the new version is healthy
- Traffic gradually shifts from old to new
- If anything looks wrong, traffic shifts back instantly

The key insight: **rollback is always one click away**. You don't need to "fix forward" under pressure. If metrics degrade, roll back first, investigate second.

### Monitoring Window

After a deploy, we watch metrics for 15 minutes:

- **Error rate**: Should stay below 0.1%. Any spike above 1% triggers rollback.
- **Latency**: P95 should stay under 500ms. Sustained increase above 1s triggers rollback.
- **Business metrics**: Order completion rate, payment success rate should stay stable.

If you're unsure whether a metric looks normal, check the dashboards linked in the [[example-service-outage-runbook|Service Outage Runbook]] for baseline comparisons.

## Common Questions

### "Can I deploy on Friday afternoon?"

We have a soft freeze Friday after 3pm. You can deploy with senior engineer approval, but ask yourself: do you want to be debugging at 7pm on a Friday?

### "What if my change needs a database migration?"

Database migrations are always high-risk. They need:
- A tested rollback migration
- Off-peak deployment window
- DBA review for anything touching indexes or large tables

See the database migration section of the [[example-production-deployment-sop|Deployment SOP]] for the exact procedure.

### "How do I know if my change is high-risk?"

If any of these are true, it's high-risk:
- Database schema changes
- New external service dependencies
- Changes to authentication or authorization
- Breaking API changes (even behind feature flags)
- Infrastructure changes (new queues, new caches, scaling config)

## Next Steps

- Read the [[example-change-management-process|Change Management Process]] to understand the governance workflow
- Bookmark the [[example-production-deployment-sop|Production Deployment SOP]] for when you're ready to deploy
- Familiarize yourself with the [[example-service-outage-runbook|Service Outage Runbook]] before your first on-call rotation
