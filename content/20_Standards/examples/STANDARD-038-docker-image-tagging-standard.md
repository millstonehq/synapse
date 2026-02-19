---
id: STANDARD-038
type: standard
title: Docker Image Tagging Standard
status: deprecated
owner: Head of Engineering
created: '2025-06-18T07:52:00.590Z'
updated: '2025-01-20T02:15:02.479Z'
tags:
  - standard
  - ci-cd-platform
summary: Docker Image Tagging Standard
related_policies:
  - POLICY-033
  - POLICY-032
example: true
related_systems:
  - SYSTEM-032
  - SYSTEM-034
---

## Area

This standard defines the required tagging conventions for Docker container images built and published by the engineering organization's CI/CD pipelines. It applies to all images pushed to internal and external container registries and governs how tags communicate version, build provenance, and promotion status. Consistent tagging enables reliable rollbacks, clear audit trails, and safe automated promotion workflows.

## Controls

- Every image built by a CI pipeline must be tagged with the full Git commit SHA at build time (e.g., `sha-a1b2c3d4`); mutable tags (e.g., `latest`) must not be used as the primary deployment reference
- Images promoted to staging must receive an additional tag in the format `staging-YYYYMMDD-<short-sha>` (e.g., `staging-20250618-a1b2c3d`)
- Images promoted to production must be tagged with a semantic version (e.g., `v1.4.2`) that matches the Git tag on the source commit; the semantic version tag is immutable once applied
- The `latest` tag may only be updated as an alias for the most recent production-promoted image; it must never be used in deployment manifests
- Images built from feature branches must be tagged with the branch name slug and commit SHA (e.g., `feat-new-auth-a1b2c3d`) and must be cleaned up from the registry within 30 days of branch deletion
- All image tags must include an accompanying OCI label `org.opencontainers.image.revision` set to the full commit SHA

## Compliance Mappings

- SLSA Level 2: Build provenance — tracing every deployed artifact to its source commit
- SOC 2 CC7.2 — System components are protected from unauthorized changes
- NIST SP 800-190: Container image tagging and provenance practices

## Related Policies

- [[POLICY-033|Deployment Approval Policy]]
- [[POLICY-032|Artifact Signing and Verification Policy]]
