---
id: POLICY-032
type: policy
title: Artifact Signing and Verification Policy
status: approved
owner: VP Engineering
created: '2024-11-21T04:11:44.610Z'
updated: '2026-01-17T08:42:02.133Z'
tags:
  - policy
  - ci-cd-platform
summary: Artifact Signing and Verification Policy
example: true
related_standards:
  - STANDARD-041
  - STANDARD-042
---

## Scope

This policy governs the signing and verification of all build artifacts produced by the engineering organization's CI/CD pipelines. It applies to container images, binary releases, deployment packages, and any artifact that is promoted from a CI pipeline to a downstream environment or registry. All teams producing deployable artifacts are subject to this policy.

Verification requirements apply at every stage where an artifact transitions across trust boundaries — including promotion from staging to production, pushes to external registries, and transfers to partner systems.

## Rationale

- Unsigned artifacts cannot be verified to originate from trusted build infrastructure, enabling substitution attacks during transit or storage
- Supply chain attacks increasingly target the gap between artifact creation and deployment; cryptographic signing closes this gap
- Verification gates prevent deployment of artifacts that were not produced by approved pipelines, even if access to the registry is compromised
- Signed artifacts create an immutable audit trail linking every deployed version to a specific pipeline run, commit SHA, and build environment
- Regulatory frameworks including SLSA and NIST SSDF require artifact integrity controls for compliant software supply chains

## Policy Statements

- All container images built by approved CI pipelines must be signed using a hardware-backed or HSM-managed signing key before being pushed to any registry
- Deployment systems must verify artifact signatures before pulling and running any container image; deployments of unsigned or unverified images must fail automatically
- Signing keys must be rotated at least annually and immediately upon suspected compromise; retired keys must be revoked in all verification stores
- A software bill of materials (SBOM) must be generated for every release artifact and attached to the signed artifact in the registry
- The signing identity (key ID, pipeline run ID, and commit SHA) must be recorded in the deployment audit log for every production deployment
- Exceptions to artifact signing requirements require documented approval from the CISO and must specify a time-bound remediation plan

## Related Standards

- [[STANDARD-041|CI/CD Secret Management Standard]]
- [[STANDARD-042|Pipeline Status Reporting Standard]]
