---
id: PROCESS-035
type: process
title: Pipeline Deprecation Process
status: deprecated
owner: Platform Lead
created: '2024-11-25T16:03:36.497Z'
updated: '2026-12-15T07:14:55.416Z'
tags:
  - process
  - data-pipeline
summary: Pipeline Deprecation Process
related_standards:
  - STANDARD-035
  - STANDARD-034
related_sops:
  - SOP-057
  - SOP-056
related_systems:
  - SYSTEM-030
example: true
---

## Purpose

This process provides a structured approach for safely decommissioning data pipelines that are no longer needed or are being replaced. It ensures downstream consumers are migrated before a pipeline is shut down, data retention obligations are met, and infrastructure is cleaned up.

## Scope

- Batch and streaming pipelines scheduled for decommissioning
- Kafka topics and consumer groups associated with deprecated pipelines
- Data lake tables or warehouse datasets produced exclusively by the deprecated pipeline
- Connector configurations and credentials tied to the deprecated pipeline

## Roles and Responsibilities

- **Pipeline Owner**: Initiates deprecation, identifies all downstream consumers, coordinates migration
- **Downstream Consumer Teams**: Acknowledge deprecation notice, confirm migration to replacement pipeline
- **Data Platform Team**: Reviews deprecation plan, deactivates infrastructure, and archives metadata
- **Data Governance**: Confirms data retention obligations are met before deletion of datasets

## Triggers

- A pipeline is being replaced by a newer implementation
- A data source is being decommissioned and the pipeline has no valid replacement source
- A pipeline has had zero active consumers for 90 days as identified by usage monitoring

## Inputs

- List of all downstream consumers identified from the data catalog and schema registry
- Replacement pipeline or dataset reference (if applicable)
- Data retention assessment confirming no outstanding obligations

## Outputs

- All downstream consumers migrated to replacement pipeline or confirmed no longer active
- Deprecated pipeline deactivated and removed from production orchestration
- Kafka topics and consumer groups deregistered
- Data catalog entry updated to `deprecated` status with retirement date

## Steps

1. Pipeline Owner creates a deprecation ticket and identifies all consumers via catalog and schema registry
2. Pipeline Owner notifies all downstream consumers with a deprecation date at least 30 days in advance
3. Downstream consumer teams confirm migration to the replacement pipeline or acknowledge no further dependency
4. Data Governance confirms all data retention periods have been met for datasets produced by the pipeline
5. Pipeline Owner pauses the pipeline and monitors for any consumer failures over a 7-day observation window
6. Data Platform Team deactivates the pipeline definition in the orchestration platform
7. Data Platform Team deregisters associated Kafka topics, consumer groups, and connector configurations
8. Data Platform Team updates the data catalog entry to deprecated and archives schema registry entries

## Controls

- Pipeline decommissioning requires written confirmation from all identified downstream consumers
- No datasets may be deleted before data retention obligations are confirmed as met
- A minimum 30-day deprecation notice is required before pipeline shutdown
- Deprecation actions must be logged in the change management system
