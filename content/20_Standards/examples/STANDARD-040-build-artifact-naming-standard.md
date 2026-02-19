---
id: STANDARD-040
type: standard
title: Build Artifact Naming Standard
status: approved
owner: Security Lead
created: '2025-06-29T16:52:50.689Z'
updated: '2026-08-09T05:14:20.203Z'
tags:
  - standard
  - ci-cd-platform
summary: Build Artifact Naming Standard
related_policies:
  - POLICY-032
  - POLICY-035
example: true
related_systems:
  - SYSTEM-034
  - SYSTEM-032
---

## Area

This standard defines naming conventions for all build artifacts produced by the CI/CD pipeline, including binary executables, compiled libraries, compressed archives, container images, Helm charts, and test reports. Consistent artifact naming enables automated promotion workflows, unambiguous rollback targeting, and reliable audit trail reconstruction. All pipeline configurations must generate artifacts conforming to this standard.

## Controls

- Artifact names must follow the pattern `<service-name>-<version>-<commit-sha-short>-<build-number>.<extension>` (e.g., `payments-api-1.4.2-a1b2c3d-142.tar.gz`)
- The `<service-name>` component must match the canonical service name registered in the service catalog; use of aliases, abbreviations, or informal names is prohibited
- The `<version>` component must be a valid semantic version (`MAJOR.MINOR.PATCH`); artifacts produced from non-release branches must use a pre-release suffix (e.g., `1.4.2-rc.1`)
- Artifact names must be lowercase and use hyphens as word separators; underscores, spaces, and camelCase are prohibited
- Test report artifacts must follow the pattern `<service-name>-test-report-<commit-sha-short>.<format>` (e.g., `payments-api-test-report-a1b2c3d.xml`)
- Artifacts must be accompanied by a corresponding SHA-256 checksum file with the suffix `.sha256`

## Compliance Mappings

- SLSA Level 1: Artifact provenance — linking artifact to build environment and source commit
- SOC 2 CC7.1 — Detection and monitoring of configuration and artifact changes
- NIST SP 800-218 (SSDF): RV.1.1 — Identify and confirm vulnerabilities within the product using artifact metadata

## Related Policies

- [[POLICY-032|Artifact Signing and Verification Policy]]
- [[POLICY-035|Release Cadence Policy]]
