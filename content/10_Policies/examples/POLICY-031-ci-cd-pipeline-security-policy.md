---
id: POLICY-031
type: policy
title: CI/CD Pipeline Security Policy
status: approved
owner: VP Engineering
created: '2025-06-04T08:24:51.996Z'
updated: '2025-08-14T10:03:39.891Z'
tags:
  - policy
  - ci-cd-platform
summary: CI/CD Pipeline Security Policy
example: true
related_standards:
  - STANDARD-037
  - STANDARD-042
---

## Scope

This policy applies to all CI/CD pipelines operated by the engineering organization, including pipelines that build, test, scan, and deploy application code, infrastructure-as-code, and container images. It covers all pipeline stages from source code commit through production deployment and applies to all engineers, automation systems, and third-party integrations that interact with the pipeline.

All environments managed by CI/CD automation — including development, staging, and production — fall within scope. Contractors and vendors with pipeline access are subject to the same requirements as full-time engineering staff.

## Rationale

- Unsecured pipelines are a common attack vector for supply chain compromise, enabling malicious code injection between commit and deployment
- Pipeline credentials and secrets are high-value targets; their exposure can grant full environment access without requiring direct system access
- Unvalidated build artifacts may contain vulnerabilities introduced through compromised dependencies or tampered toolchains
- Audit trails from pipeline activity are essential for incident investigation and regulatory compliance
- Automated enforcement of security gates in the pipeline reduces reliance on manual review and human error

## Policy Statements

- All CI/CD pipeline configurations must be stored in version-controlled repositories and subject to peer review before merging
- Pipeline jobs must run with least-privilege service accounts; no pipeline job may use credentials granting broader access than required for its specific task
- Secrets and credentials must never be embedded in pipeline configuration files; all secrets must be sourced from an approved secrets management system at runtime
- All container images built by the pipeline must undergo automated security scanning before promotion to any environment; images with critical or high-severity CVEs must not be deployed without documented exception approval
- Pipeline execution logs must be retained for a minimum of 90 days and accessible only to authorized personnel
- All production deployments must pass through a defined approval gate; automated deployments to production are permitted only when all preceding quality and security gates have passed

## Related Standards

- [[STANDARD-037|CI Pipeline Configuration Standard]]
- [[STANDARD-042|Pipeline Status Reporting Standard]]
