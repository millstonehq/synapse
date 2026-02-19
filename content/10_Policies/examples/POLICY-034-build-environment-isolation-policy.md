---
id: POLICY-034
type: policy
title: Build Environment Isolation Policy
status: proposed
owner: CISO
created: '2025-05-08T00:18:11.081Z'
updated: '2025-07-17T14:38:39.417Z'
tags:
  - policy
  - ci-cd-platform
summary: Build Environment Isolation Policy
example: true
related_standards:
  - STANDARD-037
  - STANDARD-038
---

## Scope

This policy applies to all build environments used by the engineering organization's CI/CD pipelines, including self-hosted runners, cloud-hosted build agents, and ephemeral container-based build environments. It covers both shared and dedicated build infrastructure. All teams operating or consuming CI/CD build capacity must comply with this policy.

The policy is concerned with preventing cross-contamination between builds and limiting the lateral movement potential if a build environment is compromised.

## Rationale

- Shared build environments that persist state between jobs create pathways for one build to read or tamper with another build's artifacts, secrets, or cache
- A compromised build job running in an insufficiently isolated environment can exfiltrate secrets or inject malicious code into co-tenant builds
- Build environments with access to production credentials or networks dramatically increase the blast radius of a supply chain attack
- Ephemeral environments that are destroyed after each job eliminate entire classes of persistence-based attacks
- Isolation boundaries enforce the principle of least privilege at the infrastructure level, complementing application-layer security controls

## Policy Statements

- Each CI pipeline job must execute in an isolated environment that is freshly provisioned for that job and destroyed upon completion; reuse of execution environments across jobs or repositories is prohibited
- Build environments must not have network access to production systems except for explicitly approved artifact publishing endpoints (container registry, artifact store)
- Build environments must not mount or have access to secrets that are not required for the specific job being executed; secret injection must occur at the job level, not the environment level
- Privileged container execution (Docker-in-Docker with `--privileged`) is prohibited in shared runner pools; builds requiring elevated privileges must use dedicated isolated infrastructure
- Build runner images must be sourced from organization-approved base images and rebuilt on a weekly cadence or upon discovery of critical CVEs
- Network egress from build environments must be restricted to an allowlist of approved package registries, artifact stores, and external APIs

## Related Standards

- [[STANDARD-037|CI Pipeline Configuration Standard]]
- [[STANDARD-038|Docker Image Tagging Standard]]
