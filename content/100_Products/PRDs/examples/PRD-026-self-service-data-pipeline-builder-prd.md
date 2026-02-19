---
id: PRD-026
type: prd
title: Self-Service Data Pipeline Builder PRD
status: accepted
owner: Senior PM
created: '2024-01-30T02:38:37.145Z'
updated: '2026-06-28T08:18:21.155Z'
tags:
  - prd
  - data-pipeline
summary: Self-Service Data Pipeline Builder PRD
related_tdds:
  - TDD-029
  - TDD-030
example: true
related_standards:
  - STANDARD-034
---

## Summary

Build a self-service data pipeline builder that enables data consumers (analysts, data scientists, and product engineers) to define, configure, and deploy Airflow DAGs and dbt models without direct involvement from the Data Engineering team. This replaces the current request-ticket workflow where consumers wait 2–3 weeks for Data Engineering to build new pipelines on their behalf. Technical design is driven by [[TDD-029|TDD-029: Pipeline Orchestration Service]] and [[TDD-030|TDD-030: Data Lineage Tracker]], and must comply with [[STANDARD-034|STANDARD-034]].

## Goals

- Reduce time-to-pipeline from 2–3 weeks (ticket-based) to < 2 days (self-service)
- Enable data consumers to build and manage pipelines without writing Airflow boilerplate
- Maintain pipeline quality standards (retry limits, SLA definitions, lineage tracking) through guardrails, not manual review
- Reduce Data Engineering backlog of pipeline requests by 60% within 6 months of launch

## In Scope

- Web UI for defining pipeline configurations (source topic, target Iceberg table, transformation logic, schedule, SLA window)
- dbt model scaffolding: generate a starter dbt model file from user-provided column mapping
- Airflow DAG generation from pipeline configuration, deployed via CI/CD to MWAA
- Lineage registration: automatically register pipeline in the Data Lineage Tracker on deployment
- Self-service pipeline lifecycle management: pause, resume, trigger manual run, view run history

## Out of Scope

- Custom operator development (only built-in and approved custom operators are usable)
- Cross-environment pipeline promotion (pipelines deploy to prod only after staging validation)
- Real-time streaming pipeline creation (batch/scheduled pipelines only in v1)
- Admin override of pipeline configuration guardrails (violations block deployment)

## Users and Flows

**Data Analysts**: Define transformation logic for analytical aggregations using a SQL editor; deploy dbt models against staging Iceberg tables; promote to production after data quality checks pass.

**Data Scientists**: Define feature extraction pipelines pulling from raw Iceberg tables; configure scheduled runs aligned with model training cadences.

**Product Engineers**: Register event-to-Iceberg ingestion pipelines for new product event topics; configure SLA windows aligned with downstream dashboard freshness requirements.

## Requirements

- User can define a pipeline by specifying source (Kafka topic or Iceberg table), transformation SQL, target table name, and schedule
- System validates retry settings, SLA window, and DAG naming conventions before allowing deployment
- Generated Airflow DAG must pass the existing DAG validation CI step before deployment
- Pipeline deployment triggers lineage registration in the Data Lineage Tracker
- User can view last 30 days of DAG run history and task instance logs from the UI
- Pipeline configurations are version-controlled; users can view diff and roll back to a previous version

## KPIs

- **Self-service adoption**: 60% of new pipeline requests fulfilled via self-service within 6 months of launch
- **Time-to-pipeline**: P50 < 2 days from pipeline definition to first successful production run
- **Guardrail effectiveness**: Zero DAGs deployed with policy-violating retry or SLA configurations
- **Deployment success rate**: > 95% of pipeline deployments succeed without manual intervention

## Information Architecture

- Pipeline configurations stored in the data-pipeline repository under `self-service-pipelines/` as YAML
- Generated DAG files deployed to MWAA DAG bucket via CI/CD
- Pipeline metadata indexed in the Data Lineage Tracker for lineage queries

## Data Model

Core entities:

- **PipelineDefinition**: User-authored pipeline config. Fields: `pipeline_id`, `owner`, `source_type`, `source_ref`, `transformation_sql`, `target_table`, `schedule`, `sla_window`, `version`, `created_at`
- **PipelineDeployment**: Record of each deployment attempt. Fields: `deployment_id`, `pipeline_id`, `version`, `dag_id`, `status`, `deployed_at`, `deployed_by`
- **GeneratedDAG**: Output artifact. Fields: `dag_id`, `pipeline_id`, `dag_content`, `validation_result`, `generated_at`

## Non-Functional

- Pipeline deployment end-to-end (submit → first DAG run) must complete within 10 minutes
- All pipeline configurations stored in Git with full audit trail
- Generated DAGs must be semantically equivalent to hand-authored DAGs passing the existing validation CI step
- UI must be accessible without VPN (internal SSO authentication)

## Constraints

- Must use the existing MWAA environment; cannot provision new Airflow instances
- dbt model scaffolding must use the existing dbt project structure and adapter (dbt-trino)
- Pipeline configurations must comply with data governance standards for naming conventions and SLA definitions

## Risks

- **Generated DAG quality**: Auto-generated DAGs may have edge cases the validation step does not catch. Mitigation: staging environment sandbox where each pipeline runs 3 times successfully before production promotion.
- **Adoption resistance**: Data Engineering team may be skeptical of self-service quality. Mitigation: start with a beta cohort of trusted analyst users; expand after 30-day quality validation period.
- **Configuration sprawl**: Self-service creates many more pipelines. Mitigation: pipeline deprecation policy enforced after 90 days of zero runs; auto-pause after 30 days of failures.

## Milestones

### M1: Pipeline Configuration and Validation (Week 1-4)

#### Deliverables

- Web UI for pipeline definition (source, SQL, target, schedule)
- DAG generation from pipeline YAML
- Validation CI step integration (retry limits, SLA, naming)

#### Acceptance Criteria

- User can define a pipeline and receive a generated DAG YAML for review
- Invalid configurations (e.g., retries > 5) are rejected with actionable error messages
- Generated DAG passes existing CI validation step

### M2: Deployment and Lineage (Week 5-7)

#### Deliverables

- CI/CD pipeline that deploys generated DAG to MWAA on configuration commit
- Lineage registration on deployment completion
- Staging sandbox environment with 3-run validation before production promotion

#### Acceptance Criteria

- Pipeline deploys to production in < 10 minutes from configuration commit
- Deployed pipeline appears in Data Lineage Tracker within 5 minutes of first run
- Staging sandbox blocks promotion if any of 3 validation runs fail

### M3: Lifecycle Management (Week 8-10)

#### Deliverables

- Run history and log viewer in UI (30-day window)
- Pipeline pause/resume and manual trigger
- Configuration version history and rollback

#### Acceptance Criteria

- User can view last 30 days of run history and open task logs without direct Airflow UI access
- User can roll back to a previous pipeline configuration version and redeploy in < 5 minutes
