---
id: STANDARD-042
type: standard
title: Pipeline Status Reporting Standard
status: draft
owner: Compliance Officer
created: '2024-05-28T23:15:14.277Z'
updated: '2025-12-04T12:00:56.353Z'
tags:
  - standard
  - ci-cd-platform
summary: Pipeline Status Reporting Standard
related_policies:
  - POLICY-032
  - POLICY-035
example: true
related_systems:
  - SYSTEM-035
  - SYSTEM-033
---

## Area

This standard defines the requirements for reporting pipeline execution status to developers, operators, and monitoring systems. It covers status notifications, commit status checks on pull requests, deployment event webhooks, and the structured log format that pipelines must emit. Consistent status reporting enables teams to detect pipeline failures quickly, track deployment history, and feed metrics into engineering productivity dashboards.

## Controls

- Every pipeline run must post a commit status check to the source repository (success/failure/pending) linked to the pipeline run URL; this check must be posted within 60 seconds of the pipeline completing
- Pipeline failures must trigger a Slack notification to the repository's designated team channel within 2 minutes of job failure; the notification must include the repository name, branch, failing stage name, and a direct link to the failure log
- Every production deployment must emit a structured deployment event to the central event bus containing: service name, version/commit SHA, environment, deployer identity, timestamp, and outcome (success/failure/rollback)
- Pipelines must expose a machine-readable status endpoint or artifact (e.g., a `pipeline-summary.json`) that records stage durations, test counts, coverage percentage, and security scan outcomes
- Pipeline status dashboards must be refreshed at intervals of no more than 5 minutes; stale or unavailable dashboards must trigger an alert to the platform team
- Monthly pipeline reliability reports (success rate, mean time to green, flaky test rate) must be generated automatically and published to the engineering metrics space

## Compliance Mappings

- SOC 2 CC7.2 — Monitoring and detection of anomalies in system operations
- NIST SP 800-53 AU-2 — Audit event definitions and logging
- DORA Metrics: Deployment frequency and change failure rate instrumentation

## Related Policies

- [[POLICY-032|Artifact Signing and Verification Policy]]
- [[POLICY-035|Release Cadence Policy]]
