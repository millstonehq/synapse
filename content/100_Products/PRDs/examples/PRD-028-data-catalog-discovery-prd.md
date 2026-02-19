---
id: PRD-028
type: prd
title: Data Catalog Discovery PRD
status: approved
owner: Head of Product
created: '2024-10-07T08:28:07.218Z'
updated: '2026-01-25T08:13:09.446Z'
tags:
  - prd
  - data-pipeline
summary: Data Catalog Discovery PRD
related_tdds:
  - TDD-028
  - TDD-027
example: true
related_standards:
  - STANDARD-035
---

## Summary

Build a Data Catalog Discovery product that gives all data consumers a searchable, browsable interface for discovering available Iceberg tables, understanding their schemas, viewing sample data, checking data freshness, and accessing lineage context. This replaces the current approach of browsing S3 directly, asking Data Engineering via Slack, or reading stale Confluence pages to find datasets. Technical design is driven by [[TDD-028|TDD-028: Schema Evolution Handler]] and [[TDD-027|TDD-027: Data Quality Validation Framework]], and must comply with [[STANDARD-035|STANDARD-035]].

## Goals

- Reduce time for a new team member to find and start using an appropriate dataset from 1–2 days to < 30 minutes
- Eliminate "ask Data Engineering on Slack" as the primary dataset discovery mechanism
- Provide authoritative schema documentation that stays in sync with actual table structures automatically
- Enable consumers to assess dataset quality before committing to it as a dependency

## In Scope

- Full-text search across all Iceberg table names, column names, and descriptions
- Table detail page: schema (columns, types, descriptions), data freshness (last updated), row count, partition info
- Quality status badge per table (based on most recent quality check run)
- Column lineage view: which upstream sources contributed to a column
- Data sample preview (top 10 rows, non-PII columns only)
- Tag-based browsing by domain (orders, inventory, analytics, etc.)

## Out of Scope

- Table ownership workflows (managed separately in the data governance process)
- Write access or table creation from the catalog UI
- External data source catalog (cloud provider, SaaS tool schemas)
- PII data sample previews

## Users and Flows

**Data Analysts**: Search for datasets by business concept (e.g., "orders by customer"); browse columns to find relevant metrics; check freshness before building a report; view quality score before creating a dependency.

**Data Scientists**: Discover feature candidates by browsing mart-layer tables; understand column provenance via lineage view before using a derived feature.

**New Engineers**: Onboard to the data platform by browsing available datasets organized by domain; use schema documentation to understand table structures without asking teammates.

## Requirements

- Search returns results within 2 seconds for queries against the full catalog (currently 200+ tables)
- Schema documentation is auto-populated from Iceberg table metadata and dbt column descriptions; no manual entry required for schema fields
- Quality status badge reflects the most recent quality check run (updated within 30 minutes of check completion)
- Column lineage view traverses the lineage graph from the Data Lineage Tracker API
- Data sample preview executes a Trino `SELECT ... LIMIT 10` query with column-level PII masking applied
- Tag taxonomy is defined centrally by Data Engineering; consumers cannot create new tags

## KPIs

- **Discovery time**: New team member can find and evaluate an appropriate dataset in < 30 minutes (measured by user research sessions)
- **Data Engineering Slack questions**: 50% reduction in "where can I find X data" questions within 90 days of launch
- **Catalog coverage**: 100% of production Iceberg tables indexed within 24 hours of table creation
- **Quality badge accuracy**: Quality badge matches the actual last quality check result within 30 minutes

## Information Architecture

- Catalog index built from Iceberg Glue Catalog metadata and dbt manifest column descriptions
- Quality badges read from DynamoDB quality_results (same source as Data Quality Dashboard)
- Lineage data via Data Lineage Tracker REST API
- PII column registry maintained by Data Governance team; referenced for sample preview masking

## Data Model

Core entities:

- **CatalogTable**: Indexed table entry. Fields: `table_id`, `layer`, `schema`, `table_name`, `description`, `tags`, `owner`, `row_count`, `last_updated`, `quality_score`
- **CatalogColumn**: Column entry. Fields: `table_id`, `column_name`, `data_type`, `description`, `is_pii`, `sample_values`
- **CatalogIndex**: Search index. Updated on Iceberg metadata change and dbt manifest update

## Non-Functional

- Catalog index updated automatically on each dbt run and Iceberg table metadata change
- No raw PII in sample previews; PII columns masked as `[REDACTED]`
- Authentication via SSO; no anonymous access
- Catalog reads are read-only; no writes to Iceberg tables or catalog index from the UI

## Constraints

- Must use existing Iceberg Glue Catalog as the source of truth for table metadata
- Column descriptions sourced from dbt manifest; no manual override UI
- Sample preview queries limited to 10 rows; no full-table exports from the catalog

## Risks

- **Schema drift**: If dbt manifest is not updated frequently, catalog descriptions lag table reality. Mitigation: catalog index updated on every dbt run; staleness banner shown if index is > 2 hours old.
- **PII exposure in samples**: Misconfigured PII registry could expose sensitive columns. Mitigation: default-deny policy for new columns; columns must be explicitly marked non-PII before appearing in sample previews.

## Milestones

### M1: Core Catalog and Search (Week 1-4)

#### Deliverables

- Table search with full-text index over table and column names
- Table detail page with schema from Iceberg metadata
- Auto-indexing on dbt manifest update

#### Acceptance Criteria

- Search returns relevant results within 2 seconds for any production table name
- Table detail page shows accurate schema with column types and descriptions
- Index updates within 30 minutes of a new dbt run completing

### M2: Quality, Lineage, and Samples (Week 5-7)

#### Deliverables

- Quality status badge on table and column level
- Column lineage view from Data Lineage Tracker
- Data sample preview with PII masking

#### Acceptance Criteria

- Quality badge reflects most recent check within 30 minutes
- Lineage view shows correct upstream/downstream tables to depth 3
- Sample preview masks all columns in the PII registry

### M3: Tags, Browse, and Adoption (Week 8-9)

#### Deliverables

- Tag-based browsing by domain
- Catalog coverage monitoring (alert if table uncatalogued > 24 hours)
- Team onboarding documentation and demo sessions

#### Acceptance Criteria

- All production tables browsable by domain tag
- No production table uncatalogued for > 24 hours after creation
