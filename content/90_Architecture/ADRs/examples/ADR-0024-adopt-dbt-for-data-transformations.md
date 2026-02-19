---
id: ADR-0024
type: adr
title: Adopt dbt for Data Transformations
status: approved
owner: Principal Engineer
created: '2025-08-13T13:58:53.146Z'
updated: '2026-08-30T20:12:28.471Z'
tags:
  - adr
  - data-pipeline
summary: Adopt dbt for Data Transformations
example: true
---

## Context

The data platform transformation tier previously consisted of a collection of bespoke Python ETL scripts deployed as ECS tasks. Problems with this approach accumulated over two years:

- **No lineage**: Dependencies between transformation steps were implicit; a broken upstream model had no automated downstream impact analysis
- **No testing**: Data quality tests were absent; regressions in transformation logic went undetected until consumers reported issues
- **Inconsistent materialization**: Some scripts used CTAS, others INSERT OVERWRITE, others full truncate-reload — no consistency across the ~60 transformation jobs
- **Slow iteration**: Adding a new transformation required writing and deploying a new ECS task with its own Dockerfile, IAM role, and Airflow DAG entry

The team required a transformation framework that provided: SQL-first authoring, dependency graph with lineage, automated data testing, consistent materialization strategies (incremental, snapshot, full refresh), and a CI/CD-compatible test-before-deploy workflow.

## Decision

Adopt **dbt Core** (open-source) as the transformation layer for all data lake transformation jobs.

Configuration: dbt project at `dbt/` in the data-pipeline repository. Adapter: `dbt-trino` connecting to the Trino cluster over the data lake. Profiles stored in AWS Secrets Manager, injected at ECS task runtime. Models organized in three layers: `staging/` (source-aligned, minimal transforms), `intermediate/` (join and reshape), `marts/` (business-logic aggregations for consumers). All models use `incremental` materialization by default; `full_refresh` is explicitly declared for reference tables. dbt tests (not_null, unique, accepted_values, relationships) are required for all mart-layer models before merge.

## Consequences

**Positive:**
- DAG-based dependency resolution eliminates implicit ordering bugs between transformation steps
- dbt test suite catches data quality regressions before they reach consumers
- Incremental materialization significantly reduces transformation compute cost vs. full reloads
- `dbt docs generate` produces browsable lineage and column documentation automatically
- CI pipeline runs `dbt build --select state:modified+` to test only affected models on PR

**Negative:**
- SQL-only authoring excludes complex Python-based transformations (these remain as separate ECS tasks calling into the dbt project as sources)
- dbt-trino adapter support lags behind dbt-spark and dbt-snowflake; some advanced macros require workarounds
- Incremental model logic requires careful `is_incremental()` guard discipline; incorrect implementation causes silent duplicate data
- Full dbt build time for 60+ models is approximately 45 minutes; selective builds required for development speed

**Neutral:**
- dbt Cloud was evaluated but rejected in favor of open-source dbt Core to avoid vendor lock-in and SaaS dependency
- Airflow orchestrates dbt runs via the dbt-airflow operator; dbt itself does not manage scheduling

## Alternatives Considered

**Apache Spark with custom ETL framework:**
- Pro: Maximum flexibility, Python/Scala authoring, handles non-SQL transformations natively, strong ecosystem
- Con: High operational overhead (cluster management, Spark version compatibility), slow iteration cycle, no built-in testing framework
- Rejected because: The team's SQL proficiency is higher than Spark expertise; the transformation workload is predominantly SQL-expressible

**AWS Glue ETL:**
- Pro: Managed Spark, no cluster management, native AWS integration with Glue Catalog
- Con: Vendor lock-in to AWS; Glue Spark version often 1-2 major versions behind; limited local development experience; cost unpredictable at scale
- Rejected because: Local development and CI testing workflows are critical; Glue's cloud-only execution model makes development slow

**Custom Python scripts (status quo):**
- Pro: Maximum flexibility, familiar to team, no new framework to learn
- Con: All the problems described in Context; no path to lineage, testing, or consistency without building a framework ourselves
- Rejected because: Building an in-house ETL framework would replicate dbt's features at higher cost and lower quality
