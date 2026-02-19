---
id: STANDARD-041
type: standard
title: CI/CD Secret Management Standard
status: approved
owner: Security Lead
created: '2025-06-01T15:56:45.358Z'
updated: '2026-06-09T22:53:14.543Z'
tags:
  - standard
  - ci-cd-platform
summary: CI/CD Secret Management Standard
related_policies:
  - POLICY-032
  - POLICY-034
example: true
related_systems:
  - SYSTEM-034
  - SYSTEM-035
---

## Area

This standard governs the storage, injection, rotation, and auditing of secrets used within CI/CD pipelines. Secrets covered by this standard include API keys, service account tokens, TLS certificates, database credentials, registry access tokens, and signing keys. All pipeline jobs that require access to credentials of any kind must comply with this standard.

The goal is to ensure that secrets are never exposed in plaintext in logs, configuration files, or source code, and that their lifecycle is actively managed.

## Controls

- All secrets used in CI/CD pipelines must be stored in the organization's approved secrets management system (e.g., HashiCorp Vault, AWS Secrets Manager); storage of secrets in CI platform native secret stores is permitted only as a proxy/reference to the primary secrets manager
- Secrets must be injected into pipeline jobs as environment variables at runtime; they must never be written to disk, echoed in logs, or passed as command-line arguments visible in process listings
- Each pipeline job must be granted access only to the specific secrets it requires; broad "all secrets" grants are prohibited
- Short-lived, job-scoped tokens (e.g., OIDC-federated credentials) are preferred over long-lived static credentials wherever the target system supports them
- All secret access events must generate audit log entries in the secrets management system, including which job accessed which secret and at what time
- Secrets must be rotated at least every 90 days for long-lived credentials; rotation must be automated where technically feasible

## Compliance Mappings

- NIST SP 800-53 IA-5: Authenticator Management
- SOC 2 CC6.1 — Logical and physical access controls for credentials
- CIS Benchmark for CI/CD: Secrets hygiene controls

## Related Policies

- [[POLICY-032|Artifact Signing and Verification Policy]]
- [[POLICY-034|Build Environment Isolation Policy]]
