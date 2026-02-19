---
id: STANDARD-036
type: standard
title: Data Catalog Metadata Standard
status: approved
owner: Compliance Officer
created: '2025-06-20T20:54:51.494Z'
updated: '2026-02-18T14:46:38.445Z'
tags:
  - standard
  - data-pipeline
summary: Data Catalog Metadata Standard
related_policies:
  - POLICY-030
  - POLICY-027
example: true
related_systems:
  - SYSTEM-027
  - SYSTEM-030
---

## Area

This standard defines the required metadata fields that must be registered in the organization's data catalog for all datasets promoted to production. It applies to data lake tables, data warehouse schemas, and any dataset exposed to downstream consumers via the catalog API.

## Controls

- Every production dataset must have a catalog entry containing: owner team, data classification (public/internal/confidential/restricted), update frequency, retention period, and a human-readable description
- PII-containing datasets must be labeled with the specific PII categories present (e.g., email, name, financial_id)
- Dataset lineage must be recorded, linking each dataset to its source datasets and the pipeline that produced it
- Column-level descriptions must be provided for all fields in datasets consumed by more than one team
- Catalog entries must be updated within 5 business days of any schema or ownership change
- Datasets without valid catalog entries may not be published to shared consumer environments

## Compliance Mappings

- GDPR Article 30 (Records of processing activities)
- SOC 2: CC6.1 (Asset inventory and classification)

## Related Policies

- [[POLICY-030|Data Pipeline Change Management Policy]]
- [[POLICY-027|Data Quality Gate Policy]]
