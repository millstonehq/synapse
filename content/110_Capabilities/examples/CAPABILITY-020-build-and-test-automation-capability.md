---
id: CAPABILITY-020
type: capability
title: Build and Test Automation Capability
status: approved
owner: VP Engineering
created: '2024-04-01T15:24:17.872Z'
updated: '2025-09-25T19:39:34.387Z'
tags:
  - capability
  - ci-cd-platform
summary: Build and Test Automation Capability
evidence_links:
  - STANDARD-039
  - PROCESS-041
  - POLICY-035
example: true
---

## Domain

- Build automation covering all services' CI pipelines using GitHub Actions and a self-hosted runner fleet
- Test automation including unit, integration, and end-to-end test execution in CI
- Artifact management encompassing container image builds, versioning, and storage in Harbor
- Developer tooling supporting local build parity with CI, including Dockerfile templates and shared job definitions

## Maturity (0-5)

- Build standardization: 4/5 - All services use platform-provided Dockerfile templates and GitHub Actions reusable workflows; exceptions tracked and require waiver
- Test coverage enforcement: 3/5 - Unit test coverage gates exist for most services but minimum thresholds vary by team; no fleet-wide enforcement
- Build performance: 3/5 - Average P95 build time is 8 minutes against a 7-minute target; Build Cache Service deployed but hit rate below target (68% vs 70% target)
- Artifact integrity: 4/5 - All images are Cosign-signed and Trivy-scanned; signature verification enforced at deployment gate for 95% of services
- Flaky test detection: 2/5 - Flaky tests are identified reactively when engineers notice intermittent failures; no automated detection or quarantine tooling

## Metrics

- P95 build time fleet-wide: 8 minutes (target: < 7 minutes)
- Build cache hit rate: 68% (target: > 70%)
- Fleet-wide CI pipeline pass rate: 98.4%
- Services with Cosign signature enforcement: 95% (target: 100%)
- Percentage of PRs with test coverage gate: 82% (target: 100%)

## Evidence Links

- [[STANDARD-039|STANDARD-039]] - CI/CD pipeline standards defining required gates and build conventions
- [[PROCESS-041|PROCESS-041]] - Build and test automation process documentation
- [[POLICY-035|POLICY-035]] - Policy mandating automated testing for all production services

## Notes

The biggest maturity gap is flaky test detection. Engineers spend an estimated 2 hours per week collectively investigating failures that turn out to be flaky tests rather than real regressions. Implementing a flaky test quarantine system is a Q3 priority.

Build performance is close to target but the Build Cache Service's hit rate fell below target after a base image rotation in Q1 that invalidated many cached layers. Recovery is in progress via a scheduled cache warm-up job.
