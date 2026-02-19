---
id: STANDARD-031
type: standard
title: Data Pipeline Naming Convention Standard
status: review
owner: Security Lead
created: '2025-10-17T10:25:00.101Z'
updated: '2025-08-23T09:26:43.541Z'
tags:
  - standard
  - data-pipeline
summary: Data Pipeline Naming Convention Standard
related_policies:
  - POLICY-028
  - POLICY-029
example: true
related_systems:
  - SYSTEM-030
  - SYSTEM-026
---

## Area

This standard covers naming conventions for all data pipeline artifacts within the organization, including DAG identifiers, Kafka topic names, transformation job names, connector IDs, and dataset identifiers in the data catalog. Consistent naming enables discoverability, reduces operational confusion, and supports automated tooling.

## Controls

- Pipeline names must follow the pattern `{domain}_{source}_{destination}_{frequency}` (e.g., `payments_stripe_warehouse_hourly`)
- Kafka topic names must follow the pattern `{domain}.{entity}.{event_type}` using dot-separated lowercase (e.g., `payments.transaction.created`)
- DAG IDs must be globally unique and must not be reused after deprecation
- Transformation job names must include the target dataset name and pipeline stage (e.g., `orders_raw_to_cleaned`)
- Dataset names in the data catalog must use snake_case and include a domain prefix
- Abbreviations in pipeline names are prohibited unless listed in the approved abbreviation registry

## Compliance Mappings

- SOC 2: CC6.1 (Logical access and naming controls for systems)
- ISO 27001: A.8.1.1 (Inventory of assets)

## Related Policies

- [[POLICY-028|Data Retention and Archival Policy]]
- [[POLICY-029|PII Masking in Pipelines Policy]]
