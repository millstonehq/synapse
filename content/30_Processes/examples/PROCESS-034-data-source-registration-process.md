---
id: PROCESS-034
type: process
title: Data Source Registration Process
status: draft
owner: Platform Lead
created: '2024-10-17T12:15:12.767Z'
updated: '2026-02-15T18:39:02.546Z'
tags:
  - process
  - data-pipeline
summary: Data Source Registration Process
related_standards:
  - STANDARD-036
  - STANDARD-035
related_sops:
  - SOP-056
  - SOP-055
related_systems:
  - SYSTEM-029
example: true
---

## Purpose

This process establishes a standard intake path for registering new external or internal data sources into the organization's data platform. It ensures that data sources are classified, documented, and access-controlled before any pipeline reads from them, reducing security risk and undocumented data flows.

## Scope

- New external API or SaaS data sources being connected to the ingestion layer
- New internal microservice databases being tapped for analytics replication
- New Kafka topics from internal producing services being consumed for the first time
- New file-based sources (S3, SFTP) being ingested into the data lake

## Roles and Responsibilities

- **Requesting Team**: Initiates the registration request; provides source schema, access credentials, and data classification
- **Data Platform Team**: Reviews technical feasibility, configures the connector or ingestion job, and validates connectivity
- **Data Governance**: Approves data classification, reviews PII presence, and authorizes the source for use
- **Security Team**: Reviews credential management approach and network access requirements

## Triggers

- A team requests access to a new data source for analytics or pipeline use
- A new microservice is deployed and its data is required by downstream consumers
- A data audit identifies an unregistered source currently in use

## Inputs

- Source description: system name, data type, estimated volume, and update frequency
- Sample schema or API documentation
- Data classification assessment (presence of PII, financial, or regulated data)
- Proposed credential storage approach (vault path or IAM role)

## Outputs

- Source registered in the data catalog with owner, classification, and schema
- Ingestion connector or pipeline deployed and validated
- Credentials stored in the approved secrets management system
- Access control rules applied per the [[STANDARD-036|Data Catalog Metadata Standard]]

## Steps

1. Requesting Team submits a data source registration ticket with source details and data classification assessment
2. Security Team reviews the credential management approach and network access path; approves or requests changes
3. Data Governance reviews PII classification and authorizes the source for ingestion
4. Data Platform Team configures the ingestion connector in staging and validates schema extraction
5. Data Platform Team registers the source in the data catalog with all required metadata fields
6. Data Platform Team deploys the ingestion connector to production and confirms first successful run
7. Requesting Team validates the ingested data matches expected schema and completeness
8. Data Platform Team closes the registration ticket and links it to the catalog entry

## Controls

- No pipeline may read from an unregistered data source in production
- Sources containing PII must be approved by Data Governance before ingestion begins
- Credentials for data sources must never be stored in source code or plain-text configuration
- New source registrations must be reviewed within 5 business days of submission
