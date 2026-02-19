---
id: CAPABILITY-018
type: capability
title: Data Governance Capability
status: draft
owner: VP Engineering
created: '2025-01-28T22:28:48.942Z'
updated: '2026-06-01T15:09:37.787Z'
tags:
  - capability
  - data-pipeline
summary: Data Governance Capability
evidence_links:
  - POLICY-028
  - STANDARD-032
  - STANDARD-036
example: true
---

## Domain

- Data Engineering
- Data Governance
- Security

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Level 0 - Initial**: No data governance framework. No data ownership, classification, or access control policies. Data access granted informally on request.
- **Level 1 - Ad hoc**: Some data owners are informally designated. Sensitive data classifications exist in spreadsheets but are not enforced systematically. IAM policies managed without a review process.
- **Level 2 - Repeatable** (current): Formal data classification policy (POLICY-028) and data standards (STANDARD-032, STANDARD-036) are documented and published. IAM policies for data lake roles require peer review. PII column registry exists and is referenced for query access controls. Schema Registry prevents uncoordinated schema changes. Quarterly IAM audit process in place following the March 2025 permission escalation incident.
- **Level 3 - Defined**: Data catalog lists table owners and classification for all production tables. Access control enforced via Trino column masking rules for PII columns. Lineage-based impact analysis integrated into schema change workflow. Data retention policies enforced via automated Iceberg TTL.
- **Level 4 - Managed**: Data access requests tracked in a governance workflow system. Quarterly access reviews automated. GDPR right-to-erasure workflow covers all personal data tables. Data lineage used to verify PII scope during access requests.
- **Level 5 - Optimizing**: Continuous automated policy compliance checks. ML-based PII detection for new columns. Zero-trust data access model with just-in-time elevation.

**Gap to Level 3**: Need to deploy Trino column masking rules for all PII columns in the data catalog, establish a formal table ownership assignment process, and automate Iceberg TTL for tables with defined retention policies.

## Metrics

- IAM audit completion rate (quarterly): Currently 100% (3 audits completed since March 2025 incident)
- Production IAM policies with peer review: Currently 100%, target 100%
- PII column registry coverage (mart tables): Currently 62%, target 100%
- Tables with assigned data owner in catalog: Currently 45%, target 100%
- Schema registry compatibility enforcement violations blocked per month: Currently 12, (indicates value — blocked breaking changes)
- Data retention policies with automated enforcement: Currently 0%, target 50% by end of year

## Evidence Links

- [[POLICY-028|POLICY-028]] - Data governance policy establishing data ownership, classification, and access control requirements
- [[STANDARD-032|STANDARD-032]] - Data lake access control standards including IAM role patterns and Trino permission boundaries
- [[STANDARD-036|STANDARD-036]] - Data retention and lifecycle management standards for Iceberg tables

## Notes

The organization advanced from Level 1 to Level 2 in Q2 2025, driven primarily by the March 2025 IAM permission escalation incident (POSTMORTEM-030) which exposed the absence of a structured IAM review process. The quarterly IAM audit was the key control added.

Key improvements needed for Level 3:
- Deploy Trino column masking rules for all columns in the PII registry (engineering effort estimated at 2 weeks)
- Launch the data catalog with table ownership fields and drive 100% coverage via a 60-day assignment sprint
- Implement Iceberg TTL policies for tables with defined retention periods (orders: 7 years, session events: 2 years)
