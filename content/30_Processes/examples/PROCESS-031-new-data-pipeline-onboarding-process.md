---
id: PROCESS-031
type: process
title: New Data Pipeline Onboarding Process
status: approved
owner: Director of Engineering
created: '2024-09-11T21:08:41.967Z'
updated: '2026-05-28T00:28:48.038Z'
tags:
  - process
  - data-pipeline
summary: New Data Pipeline Onboarding Process
related_standards:
  - STANDARD-032
  - STANDARD-031
related_sops:
  - SOP-051
  - SOP-060
related_systems:
  - SYSTEM-026
example: true
---

## Purpose

This process ensures that all new data pipelines are properly reviewed, registered, and instrumented before entering production. It reduces the risk of unmonitored pipelines, undocumented data flows, and schema conflicts by establishing a consistent intake path for all new pipeline work.

## Scope

- New batch and streaming pipeline definitions entering production for the first time
- New Kafka topic creation and consumer group registration
- New dbt models or transformation jobs connecting to shared datasets
- Data source connections to previously unregistered external systems

## Roles and Responsibilities

- **Pipeline Author**: Designs the pipeline, writes tests, completes the onboarding checklist, and submits for review
- **Data Platform Team**: Reviews the pipeline design for compliance with naming, monitoring, and idempotency standards; approves for production
- **Data Governance**: Reviews and approves the catalog metadata entry and data classification
- **On-Call Engineer**: Confirms alerting and dashboards are in place before pipeline goes live

## Triggers

- A new data pipeline is ready for promotion from staging to production
- A new Kafka topic or consumer group is required for an approved feature
- An existing pipeline is cloned or substantially restructured (triggers re-onboarding)

## Inputs

- Pipeline code in a reviewed and approved pull request
- Completed onboarding checklist covering naming, testing, monitoring, and catalog registration
- Schema registered in the schema registry (for event-driven pipelines)

## Outputs

- Production pipeline deployed and emitting metrics
- Data catalog entry registered with owner, classification, and lineage
- Alerting rules active in PagerDuty
- Pipeline documented in the [[STANDARD-032|Event Schema Registry Standard]] if applicable

## Steps

1. Pipeline Author completes the pipeline onboarding checklist and attaches it to the PR
2. Pipeline Author registers the output schema in the schema registry and records the schema ID
3. Data Platform Team reviews the PR for compliance with naming, idempotency, and monitoring standards
4. Data Governance reviews and approves the data catalog entry including PII classification
5. Pipeline Author configures monitoring dashboards and alerting rules; On-Call Engineer verifies coverage
6. Pipeline Author deploys to staging and validates end-to-end with a sample dataset
7. Data Platform Team approves promotion to production; Pipeline Author executes production deployment
8. Pipeline Author confirms first production run completes successfully and closes the onboarding ticket

## Controls

- No pipeline may be deployed to production without a completed onboarding checklist
- Schema registry entry is required for all event-driven pipelines before deployment
- Catalog metadata must be approved before the pipeline produces data consumed by other teams
- All new pipelines must have at least one alerting rule active on day of launch
