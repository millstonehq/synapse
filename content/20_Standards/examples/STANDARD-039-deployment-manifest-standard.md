---
id: STANDARD-039
type: standard
title: Deployment Manifest Standard
status: proposed
owner: Compliance Officer
created: '2025-03-11T03:02:54.813Z'
updated: '2026-01-27T03:11:20.719Z'
tags:
  - standard
  - ci-cd-platform
summary: Deployment Manifest Standard
related_policies:
  - POLICY-032
  - POLICY-035
example: true
related_systems:
  - SYSTEM-033
  - SYSTEM-032
---

## Area

This standard covers the required structure, content, and maintenance practices for deployment manifests used by the engineering organization. Deployment manifests include Kubernetes manifests (Deployments, Services, ConfigMaps, HorizontalPodAutoscalers), Helm chart values files, and ArgoCD Application resources. The standard ensures manifests are self-describing, auditable, and safe for automated GitOps-driven reconciliation.

## Controls

- Every Deployment manifest must include the following labels: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`, and `app.kubernetes.io/part-of`
- Container image references in manifests must use immutable tags (full commit SHA or semantic version); use of the `latest` tag or any other mutable tag in a manifest is prohibited
- Resource requests and limits (CPU and memory) must be explicitly defined for every container; manifests without resource constraints must not be merged
- Liveness and readiness probes must be configured for every container that serves network traffic; probe endpoints must not require authentication
- Deployment manifests must be stored in a dedicated GitOps repository separate from application source code and must be subject to mandatory peer review before merge
- All manifest changes must reference the associated change ticket ID in a commit message annotation

## Compliance Mappings

- NIST SP 800-190: Container orchestration security — resource isolation and configuration hygiene
- SOC 2 CC6.6 — Logical access controls for infrastructure configuration
- CIS Kubernetes Benchmark: Pod security configuration requirements

## Related Policies

- [[POLICY-032|Artifact Signing and Verification Policy]]
- [[POLICY-035|Release Cadence Policy]]
