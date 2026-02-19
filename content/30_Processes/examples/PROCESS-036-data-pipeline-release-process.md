---
id: PROCESS-036
type: process
title: Data Pipeline Release Process
status: approved
owner: Director of Engineering
created: '2024-10-14T15:56:22.827Z'
updated: '2026-06-17T23:34:39.999Z'
tags:
  - process
  - data-pipeline
summary: Data Pipeline Release Process
related_standards:
  - STANDARD-034
  - STANDARD-036
related_sops:
  - SOP-053
  - SOP-055
related_systems:
  - SYSTEM-030
example: true
---

## Purpose

This process defines the steps required to safely release changes to production data pipelines, including DAG updates, transformation logic changes, schema updates, and infrastructure configuration changes. It ensures that releases are reviewed, tested, traceable, and reversible.

## Scope

- Changes to production DAG definitions in Airflow, Dagster, or equivalent orchestrators
- Updates to dbt models, Spark jobs, or custom transformation code deployed to production
- Schema changes requiring coordination with consumers via the schema registry
- Kafka connector configuration updates in production

## Roles and Responsibilities

- **Release Engineer**: Owns the release ticket, coordinates approvals, executes the deployment
- **Peer Reviewer**: Reviews the code change and deployment plan; approves for low-risk releases
- **Senior Engineer**: Required approval for schema-breaking or high-risk pipeline changes
- **On-Call Data Engineer**: Monitors pipeline execution and data quality metrics post-release

## Triggers

- A pull request touching production pipeline code is approved and merged to main
- A scheduled batch release window includes pending pipeline changes
- An urgent data fix requires an expedited release outside normal windows

## Inputs

- Approved pull request with passing CI (tests, linting, idempotency validation)
- Release ticket with risk classification and documented rollback plan
- Schema registry compatibility check result (for schema changes)

## Outputs

- Updated pipeline deployed and executing successfully in production
- Release ticket closed with deployment evidence (commit SHA, first successful run timestamp)
- Updated data catalog metadata if output schema or lineage changed

## Steps

1. Release Engineer creates a release ticket, selects risk level, and documents the rollback plan
2. Peer Reviewer verifies CI is green, tests cover the changed logic, and the rollback plan is valid
3. Senior Engineer approves (required for schema-breaking changes or new pipeline deployments)
4. Release Engineer announces the release in #data-releases and confirms On-Call Data Engineer is available
5. Release Engineer deploys the change to the orchestration platform and triggers a test run
6. On-Call Data Engineer monitors the first post-release pipeline execution for errors and data quality
7. Release Engineer confirms successful execution and closes the release ticket with evidence
8. On-Call Data Engineer continues monitoring for the next 3 scheduled runs to catch delayed failures

## Controls

- No pipeline release without a completed release ticket linked to the approved PR
- Schema-breaking changes require senior engineer approval and consumer notification
- All releases must have a tested rollback procedure documented before execution
- Failed first post-release run must trigger immediate rollback assessment
