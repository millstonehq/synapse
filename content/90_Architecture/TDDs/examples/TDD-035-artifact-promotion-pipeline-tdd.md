---
id: TDD-035
type: tdd
title: Artifact Promotion Pipeline TDD
status: accepted
owner: Principal Engineer
created: '2025-03-06T04:32:29.686Z'
updated: '2025-08-23T03:52:12.226Z'
tags:
  - tdd
  - ci-cd-platform
summary: Artifact Promotion Pipeline TDD
related_adrs:
  - ADR-0026
  - ADR-0029
example: true
---

## Summary

Design the Artifact Promotion Pipeline, a gate-enforced workflow that moves container image artifacts from the `dev` registry repository to `staging` and then to `production` repositories in Harbor, with automated vulnerability scan verification at each gate. An image can only be deployed to a higher environment after it has passed the gates at all lower environments. The pipeline replaces the current convention-based approach where engineers manually push tags between repositories.

This design builds on the Harbor container registry selected in [[ADR-0029|ADR-0029]] and integrates with the ArgoCD deployment model adopted in [[ADR-0026|ADR-0026]].

## Overview

- **Immutable artifacts**: Images are tagged by commit SHA at build time; the promotion pipeline copies the digest (not re-tags) between repositories, ensuring the exact same bits are deployed at each stage
- **Gate checks**: Each promotion gate verifies that the image has a clean Trivy vulnerability scan, a valid Cosign signature, and (for prod promotion) a passing canary analysis result in staging
- **ArgoCD manifest update**: On successful promotion, the pipeline opens a pull request to the Kubernetes manifest repository updating the image tag for the target environment; ArgoCD syncs when the PR is merged
- **Promotion history**: Every promotion event is recorded with the image digest, promoter identity, gate results, and timestamp; accessible via the Release Dashboard
- **Rollback path**: Promoting an older image digest through the same pipeline is the standard rollback path; no special rollback tooling is required

## Architecture

- **Promotion Orchestrator**: A GitHub Actions workflow (`promote.yml`) that accepts service name and commit SHA as inputs, executes gate checks in sequence, and triggers the manifest PR on success
- **Harbor Replication Rule**: Configured promotion creates a one-time replication job in Harbor to copy the image blob between project repositories; triggered via Harbor API from the orchestrator
- **Gate Executor**: A shared composite action that wraps Trivy scan, Cosign verification, and (for prod) canary analysis result lookup; returns pass/fail with structured evidence
- **Manifest PR Writer**: A step that clones the Kubernetes manifest repository, updates the image tag in the target environment's Kustomize overlay, and opens a PR against the manifest repo's main branch
- **Promotion Event Publisher**: Posts promotion records to the Release Dashboard HTTP API after each successful gate for audit trail and dashboard display

## Information Model

- **PromotionRecord**: `id`, `service_name`, `image_digest`, `from_repo`, `to_repo`, `promoter`, `gate_results` (JSON array of GateResult), `status`, `promoted_at`
- **GateResult**: `gate_name`, `passed`, `evidence_url`, `executed_at` — one record per gate check within a promotion event
- **ManifestPR**: `id`, `promotion_record_id`, `pr_url`, `target_environment`, `target_manifest_path`, `merged_at`
- **PromotionPolicy**: Per-service configuration specifying which gates are required for each tier transition; stored as YAML in the platform config repository

## Interfaces

- GitHub Actions workflow input trigger: `workflow_dispatch` with `service`, `commit_sha`, `target_env` inputs
- Harbor Replication API: `POST /api/v2.0/replication/executions` — triggers replication between Harbor projects
- Trivy scan API or CLI: `trivy image --format json --exit-code 1 --severity CRITICAL` — used in gate check
- Cosign verify CLI: `cosign verify --key k8s://cosign-keys/cosign.pub {image}` — signature verification gate
- Release Dashboard HTTP API: `POST /v1/promotions` — publishes promotion event for audit logging

## Files and Layout

```
.github/workflows/
  promote.yml                   - Main promotion workflow definition
  actions/
    gate-check/action.yml       - Composite action for vulnerability + signing gates
    manifest-pr/action.yml      - Composite action for manifest repo PR creation
scripts/
  promotion/
    harbor_replicate.sh         - Harbor replication API call wrapper
    trivy_gate.sh               - Trivy scan invocation and result parsing
    cosign_gate.sh              - Cosign verification wrapper
    canary_gate.sh              - Canary analysis result lookup from Release Dashboard
config/
  promotion_policies/           - Per-service PromotionPolicy YAML files
```

## Work Plan

1. **Phase 1 - Harbor Replication Integration (Week 1)**: Implement harbor_replicate.sh; test dev→staging replication for one pilot service; validate image digest parity
2. **Phase 2 - Gate Checks (Week 2-3)**: Implement trivy_gate.sh and cosign_gate.sh as composite actions; wire into promote.yml with pass/fail handling
3. **Phase 3 - Manifest PR Writer (Week 3-4)**: Implement manifest PR creation for staging and production environments; test in staging with manual merge
4. **Phase 4 - Canary Gate (Week 5)**: Integrate canary analysis result lookup for production promotion gate; end-to-end test with a real canary run
5. **Phase 5 - Release Dashboard Integration (Week 6)**: Post promotion events to Release Dashboard API; display in promotion history view
6. **Phase 6 - Rollout (Week 7-8)**: Migrate all services to use promotion pipeline; deprecate manual ECR push scripts; update deployment runbooks

## Risks and Mitigations

- **Risk**: Harbor replication is slow for large images, causing promotion workflows to time out. **Mitigation**: Use async replication with polling; set GitHub Actions step timeout to 30 minutes; alert if replication exceeds 20 minutes.
- **Risk**: Manifest repository becomes a bottleneck if multiple services are promoted simultaneously and PR merges conflict. **Mitigation**: Use separate overlay directories per service so PRs do not conflict; automate PR auto-merge via Mergify when CI passes.
- **Risk**: A CVE is discovered after promotion to production but the image is already deployed. **Mitigation**: Trivy scans run nightly against all deployed image digests; critical CVE alerts page the on-call engineer for expedited hotfix or rollback.
