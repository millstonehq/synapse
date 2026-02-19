---
id: STANDARD-026
type: standard
title: Search Index Schema Standard
status: proposed
owner: Security Lead
created: '2024-04-22T00:03:02.338Z'
updated: '2026-01-26T16:10:14.736Z'
tags:
  - standard
  - search-platform
summary: Search Index Schema Standard
related_policies:
  - POLICY-021
  - POLICY-023
example: true
related_systems:
  - SYSTEM-024
  - SYSTEM-022
---

## Area

This standard governs the design, versioning, and evolution of Elasticsearch index mappings used by the Search Platform. It applies to all indexes in production and staging environments, covering field type selection, analyzer assignments, dynamic mapping rules, and the process for applying breaking and non-breaking mapping changes.

## Controls

- All index mappings must be defined in version-controlled JSON mapping files before the index is created in any environment
- Dynamic mapping must be disabled (`"dynamic": "strict"`) on all production indexes to prevent unintended field creation
- Text fields intended for full-text search must explicitly specify an analyzer; defaulting to the `standard` analyzer is not acceptable for multilingual content
- Keyword fields must have `ignore_above: 512` set to prevent indexing failures on long values
- Breaking mapping changes (field type changes, field removal) require a full reindex with the alias swap pattern; in-place mapping updates are prohibited for breaking changes
- Index aliases must be used for all production query traffic; direct index name queries are only permitted during reindex operations

## Compliance Mappings

- NIST SP 800-53: CM-2 (Baseline Configuration) - index mappings as configuration artifacts under version control
- SOC 2 CC6.1: Logical access controls enforced through index-level read/write role assignments

## Related Policies

- [[POLICY-021|Search Data Indexing Policy]]
- [[POLICY-023|Search Query Logging Policy]]
