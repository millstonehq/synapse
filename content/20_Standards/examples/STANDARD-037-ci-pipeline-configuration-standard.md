---
id: STANDARD-037
type: standard
title: CI Pipeline Configuration Standard
status: proposed
owner: Compliance Officer
created: '2024-04-06T03:56:56.237Z'
updated: '2026-09-24T05:26:03.364Z'
tags:
  - standard
  - ci-cd-platform
summary: CI Pipeline Configuration Standard
related_policies:
  - POLICY-035
  - POLICY-034
example: true
related_systems:
  - SYSTEM-032
  - SYSTEM-034
---

## Area

This standard covers the structural and behavioral requirements for CI pipeline configuration files across all repositories in the engineering organization. It applies to pipeline definitions written in YAML or equivalent formats for platforms such as GitHub Actions, GitLab CI, and Jenkins, and governs how stages, jobs, caching, artifact handling, and notification hooks are configured.

Adherence to this standard ensures pipelines are consistent, maintainable, auditable, and safe to execute in shared runner infrastructure.

## Controls

- Every repository containing deployable code must define a CI pipeline configuration file in the root directory under a recognized path (e.g., `.github/workflows/`, `.gitlab-ci.yml`)
- Pipelines must define at minimum the following stages in order: lint, test, build, security-scan, and publish; stages may not be skipped except via a documented override mechanism requiring manager approval
- All jobs must specify explicit `timeout-minutes` values; jobs without timeouts are prohibited to prevent runner pool starvation
- Pipeline configurations must not contain hardcoded credentials, API keys, or environment-specific URLs; all such values must reference named secrets or environment variables injected at runtime
- Caching configurations must scope cache keys to the specific dependency manifest file (e.g., `package-lock.json`, `go.sum`) to prevent stale cache poisoning across branches
- Pipelines must emit status notifications to the designated Slack channel on failure; success notifications are optional but recommended for production deploys

## Compliance Mappings

- NIST SP 800-218 (SSDF): PW.4.1 — Use automated tools to check code for vulnerabilities and weaknesses
- SOC 2 CC8.1 — Infrastructure changes are authorized, tested, approved, and deployed consistently
- ISO 27001 A.14.2.2 — System change control procedures

## Related Policies

- [[POLICY-035|Release Cadence Policy]]
- [[POLICY-034|Build Environment Isolation Policy]]
