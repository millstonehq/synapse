---
id: POLICY-026
type: policy
title: Data Pipeline Access Control Policy
status: approved
owner: CISO
created: '2025-05-12T02:19:30.991Z'
updated: '2025-06-13T21:19:50.625Z'
tags:
  - policy
  - data-pipeline
summary: Data Pipeline Access Control Policy
example: true
related_standards:
  - STANDARD-034
  - STANDARD-031
---

## Scope

This policy applies to all data pipeline systems, services, and infrastructure operated by the engineering organization. It covers read and write access to pipeline orchestration platforms (Airflow, Dagster), message brokers (Kafka), data lake storage, and transformation compute environments. The policy governs access for engineers, data scientists, contractors, and automated service accounts.

## Rationale

- Unrestricted access to pipeline systems enables unauthorized data exfiltration or accidental data corruption
- Service accounts with overly broad permissions are a common attack vector in data infrastructure
- Audit trails for pipeline access are required for SOC 2 and GDPR compliance
- Least-privilege access reduces the blast radius of compromised credentials

## Policy Statements

- All pipeline system access must be provisioned through the identity management platform with an approved access request
- Service accounts must be scoped to the minimum permissions required for their pipeline function
- No direct database or object-store write access is permitted without pipeline orchestration layer enforcement
- Pipeline credentials must not be stored in source code repositories or unencrypted configuration files
- Access reviews for pipeline service accounts must be conducted quarterly
- Privileged access (admin-level pipeline configuration) requires multi-factor authentication

## Related Standards

- [[STANDARD-034|Data Transformation Testing Standard]]
- [[STANDARD-031|Data Pipeline Naming Convention Standard]]
