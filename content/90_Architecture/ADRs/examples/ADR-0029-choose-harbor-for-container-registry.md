---
id: ADR-0029
type: adr
title: Choose Harbor for Container Registry
status: accepted
owner: Principal Engineer
created: '2025-08-28T04:53:40.094Z'
updated: '2026-06-11T09:13:56.793Z'
tags:
  - adr
  - ci-cd-platform
summary: Choose Harbor for Container Registry
example: true
---

## Context

Container images for all production services were stored in Amazon ECR across multiple AWS accounts, with no unified access control model. Teams managed their own ECR repositories with varying permission configurations. Several problems had emerged: there was no vulnerability scanning integrated into the pull path (images with known CVEs were deployed undetected), there was no artifact retention or promotion model (every image tag persisted indefinitely, resulting in unbounded storage growth), and ECR's per-repository IAM policies made it difficult to enforce organization-wide rules consistently.

The CI/CD Platform team was tasked with selecting a self-managed or managed container registry that could serve as a single source of truth for all build artifacts, enforce image signing and vulnerability scanning, and support a promotion model where images are explicitly promoted from dev to staging to production repositories rather than shared across environments by tag convention.

Three options were evaluated: Harbor (self-hosted CNCF project), Amazon ECR with enhanced security features, and JFrog Artifactory. The evaluation ran over six weeks with a proof-of-concept deployment of Harbor and Artifactory against a representative workload of 500 image pushes and pulls per day.

## Decision

Adopt **Harbor** as the central container registry for all production container images.

Harbor will be deployed in high-availability mode on the platform Kubernetes cluster with an external PostgreSQL database and S3-compatible object storage for layer persistence. Vulnerability scanning will use Trivy integration with a policy that blocks image promotion if critical CVEs are present. Image signing will be enforced using Cosign; the Deployment Controller will verify signatures before allowing image pulls. Repositories will be organized by environment tier (dev, staging, prod) with RBAC policies restricting promotion to CI service accounts only.

## Consequences

**Positive:**
- Integrated vulnerability scanning with Trivy blocks images with critical CVEs from reaching production
- Native image signing and verification via Cosign integration provides supply chain security
- Unified RBAC model allows organization-wide access control policies rather than per-repository IAM
- Harbor's promotion replication rules enforce the dev → staging → prod promotion model without custom tooling

**Negative:**
- Self-hosting Harbor requires the platform team to operate and maintain the registry infrastructure (HA PostgreSQL, backups, upgrades)
- Harbor's garbage collection has known edge cases that require careful tuning; an unconfigured GC job can cause database corruption (as documented in POSTMORTEM-033)
- Initial migration of all ECR images and updating of all CI pipelines is a significant one-time effort

**Neutral:**
- Storage costs are comparable to ECR at current image volume; S3-backed storage pricing is predictable
- Harbor is a CNCF graduated project with active development and regular security patches

## Alternatives Considered

**Amazon ECR with enhanced features (scanning, lifecycle policies):**
- Pro: Managed service with no operational overhead, native AWS IAM integration, Inspector-based vulnerability scanning
- Con: ECR lacks a native image promotion model across accounts; achieving the desired dev/staging/prod separation requires complex cross-account replication rules. No built-in image signing enforcement. Vendor lock-in to AWS.
- Rejected because: ECR's promotion model limitations and the absence of native Cosign signing verification did not meet the supply chain security requirements.

**JFrog Artifactory:**
- Pro: Enterprise-grade registry with excellent multi-format support (Docker, Helm, npm, Maven), strong promotion pipelines, advanced security features
- Con: License cost at our scale was $45,000/year, more than 3x the estimated Harbor infrastructure cost. The additional capabilities (multi-format artifact management) were beyond the current scope.
- Rejected because: Cost was prohibitive for a scope limited to container images. Artifactory's value proposition is strongest when consolidating multiple artifact types, which is a future consideration.
