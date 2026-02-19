---
id: PROCESS-032
type: process
title: Schema Evolution Process
status: approved
owner: Platform Lead
created: '2024-04-02T17:19:55.836Z'
updated: '2025-12-07T11:24:09.429Z'
tags:
  - process
  - data-pipeline
summary: Schema Evolution Process
related_standards:
  - STANDARD-031
  - STANDARD-033
related_sops:
  - SOP-057
  - SOP-058
related_systems:
  - SYSTEM-027
example: true
---

## Purpose

This process governs the lifecycle of schema changes for events and datasets in production pipelines. It ensures that schema evolution is coordinated with downstream consumers, validated against compatibility rules, and deployed without causing consumer failures or data loss.

## Scope

- Changes to Avro, Protobuf, or JSON Schema definitions registered in the schema registry
- Changes to dbt model column definitions that alter downstream contract expectations
- Changes to data lake table schemas used by multiple consumer teams
- Addition or removal of fields in Kafka topic payloads

## Roles and Responsibilities

- **Schema Owner**: Proposes the change, assesses backward compatibility, identifies all downstream consumers
- **Schema Registry Maintainer**: Reviews compatibility rules, registers the new schema version, enforces the policy gates
- **Downstream Consumer Teams**: Review proposed changes, confirm they can handle the new schema, sign off before deployment
- **Data Platform Team**: Approves breaking changes after verifying migration plans are in place

## Triggers

- A new field is required in an existing event or dataset schema
- A field type change is needed for correctness or optimization
- A field must be removed following a deprecation period
- A schema conflict is detected between producer and consumer versions

## Inputs

- Proposed schema definition with field-level diff from the current version
- Compatibility check result from the schema registry validation API
- List of all known downstream consumers identified from the registry

## Outputs

- New schema version registered and active in the schema registry
- All downstream consumers confirmed compatible or migrated
- Schema changelog updated with rationale and migration notes

## Steps

1. Schema Owner proposes the change and runs compatibility check against the registry API
2. Schema Owner identifies all downstream consumers from the registry and notifies them of the proposed change
3. Downstream consumer teams review the diff and confirm compatibility or request a migration window
4. Schema Registry Maintainer validates compatibility mode compliance and approves the new version
5. Schema Owner registers the new schema version in staging and deploys the producer change
6. Schema Owner validates consumers can process both old and new versions during transition
7. After all consumers have migrated, Schema Owner sets the old version as deprecated
8. Data Platform Team approves removal of deprecated version after the retention period expires

## Controls

- Schema changes must not be deployed to production without passing the registry compatibility check
- Breaking schema changes require sign-off from all identified downstream consumer teams
- Deprecated schema versions must remain available for a minimum of 14 days before removal
- All schema change decisions must be recorded in the registry changelog
