---
id: STANDARD-034
type: standard
title: Data Transformation Testing Standard
status: approved
owner: Security Lead
created: '2024-01-04T19:14:52.682Z'
updated: '2026-10-07T10:10:08.889Z'
tags:
  - standard
  - data-pipeline
summary: Data Transformation Testing Standard
related_policies:
  - POLICY-027
  - POLICY-030
example: true
related_systems:
  - SYSTEM-029
  - SYSTEM-026
---

## Area

This standard establishes testing requirements for all data transformation logic deployed within the organization's data pipelines. It covers unit tests for transformation functions, integration tests for pipeline stages, and contract tests for schema compatibility between producers and consumers.

## Controls

- All transformation functions must have unit tests covering the happy path, null inputs, and boundary values
- Integration tests must run against a representative sample dataset and validate output schema and row count expectations
- New transformations must achieve a minimum of 80% branch coverage before merging to main
- Contract tests must be run as part of CI for any change touching a shared schema or output dataset
- dbt models must have at minimum `not_null` and `unique` tests on primary key columns
- Test suites must complete within 10 minutes in CI; long-running tests must be parallelized or moved to a separate pipeline

## Compliance Mappings

- SOC 2: CC8.1 (Change management controls including testing requirements)
- ISO 27001: A.14.2.8 (System security testing)

## Related Policies

- [[POLICY-027|Data Quality Gate Policy]]
- [[POLICY-030|Data Pipeline Change Management Policy]]
