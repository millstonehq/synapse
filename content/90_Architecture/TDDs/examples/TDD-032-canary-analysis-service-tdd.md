---
id: TDD-032
type: tdd
title: Canary Analysis Service TDD
status: approved
owner: Principal Engineer
created: '2024-11-12T10:08:05.969Z'
updated: '2025-05-14T22:44:25.091Z'
tags:
  - tdd
  - ci-cd-platform
summary: Canary Analysis Service TDD
related_adrs:
  - ADR-0028
  - ADR-0027
example: true
---

## Summary

Design the Canary Analysis Service, a component that automatically evaluates in-progress canary deployments by comparing error rates, latency percentiles, and custom business metrics between the canary pod subset and the stable baseline. The service integrates with ArgoCD Rollouts to emit pass/fail decisions that allow automated promotion or rollback without human intervention.

This design implements the canary deployment strategy referenced in [[ADR-0028|ADR-0028]] and supports the automated deployment promotion workflow designed in [[ADR-0027|ADR-0027]].

## Overview

- **Metric collection**: Queries Prometheus for service-level metrics from canary and baseline pod label selectors over a configurable analysis window
- **Statistical comparison**: Uses proportional error rate comparison and Mann-Whitney U test for latency distributions to determine if the canary is statistically worse than baseline
- **Pass/fail decision**: Emits an `AnalysisRun` result to the ArgoCD Rollouts controller; a pass promotes the canary, a fail triggers automatic rollback
- **Configurable thresholds**: Per-service analysis templates define metric queries, thresholds, and minimum observation windows
- **Webhook notification**: Posts analysis results to Slack and records decisions in the Release Dashboard audit log

## Architecture

- **Analysis Controller**: A Kubernetes controller that watches `AnalysisRun` CRs created by ArgoCD Rollouts; dispatches analysis jobs when a run transitions to `Running`
- **Metric Fetcher**: Calls the Prometheus API to collect canary and baseline time-series data for the configured metrics; handles missing data by returning an `Inconclusive` result rather than failing
- **Decision Engine**: Applies threshold comparisons and statistical tests against fetched metrics; produces a structured decision with per-metric scores and an aggregate verdict
- **Result Publisher**: Patches the `AnalysisRun` status field with the decision; publishes a summary event to the Release Dashboard Service via HTTP
- **Configuration Store**: Reads `AnalysisTemplate` CRDs from the cluster namespace to determine which metrics and thresholds apply to a given service

## Information Model

- **AnalysisTemplate**: Kubernetes CRD defining metric queries, thresholds, and observation window for a service; one template per service or shared across a service group
- **AnalysisRun**: Kubernetes CRD instance created by ArgoCD Rollouts for each canary promotion attempt; references the template and includes canary/baseline pod selectors
- **MetricResult**: Internal struct recording the fetched values, computed statistics, threshold comparison, and per-metric pass/fail for a single metric in an analysis run
- **AnalysisDecision**: Aggregate struct combining all MetricResults into a final `Pass`, `Fail`, or `Inconclusive` verdict with reasoning for audit logging
- **AnalysisEvent**: Persisted record written to the Release Dashboard with the decision, run ID, service name, canary revision, and timestamp

## Interfaces

- `GET /healthz` - Liveness and readiness probe; verifies Prometheus connectivity
- `POST /v1/analysis/run/{runID}/evaluate` - Trigger immediate evaluation of a named AnalysisRun (used for manual re-evaluation)
- `GET /v1/analysis/run/{runID}` - Retrieve decision history and per-metric results for a completed run
- Kubernetes controller watch on `AnalysisRun` objects in configured namespaces — primary trigger mechanism
- Prometheus HTTP API client — outbound dependency for metric collection

## Files and Layout

```
cmd/canary-analysis/main.go     - Entry point, controller startup
internal/
  controller/                   - Kubernetes controller watching AnalysisRun CRs
  analysis/
    fetcher.go                  - Prometheus metric collection
    engine.go                   - Decision logic, statistical tests
    decision.go                 - AnalysisDecision model and verdict types
  publisher/
    argocd.go                   - Patches AnalysisRun status via K8s API
    dashboard.go                - Posts events to Release Dashboard
  config/
    template_reader.go          - Reads AnalysisTemplate CRDs from cluster
deploy/
  crds/                         - AnalysisTemplate CRD definition
  helm/                         - Helm chart for the analysis service
```

## Work Plan

1. **Phase 1 - CRD and Controller Scaffold (Week 1-2)**: Define AnalysisTemplate and AnalysisRun CRDs; implement controller watch loop; wire up basic status patching
2. **Phase 2 - Metric Fetcher (Week 2-3)**: Implement Prometheus API client; support error rate and latency queries; handle missing data and scrape gaps gracefully
3. **Phase 3 - Decision Engine (Week 3-4)**: Implement threshold comparison; add Mann-Whitney U test for latency distributions; write unit tests with synthetic metric data
4. **Phase 4 - Integration with ArgoCD Rollouts (Week 5)**: End-to-end test against a real ArgoCD Rollouts canary in staging; validate that pass/fail decisions trigger correct promotion/rollback behavior
5. **Phase 5 - Observability and Audit (Week 6)**: Add Release Dashboard event publishing; Prometheus metrics for analysis latency and decision distribution; Grafana dashboard
6. **Phase 6 - Hardening (Week 7)**: Load test with 50 concurrent AnalysisRuns; tune controller queue depth; production rollout with 10 pilot services

## Risks and Mitigations

- **Risk**: Prometheus is unavailable during an analysis window, producing Inconclusive results that block automated promotion. **Mitigation**: Implement retry with backoff; after 3 retries, fail-safe to Inconclusive (requiring manual promotion) rather than auto-fail.
- **Risk**: Statistical tests produce false positives for low-traffic canaries where sample sizes are small. **Mitigation**: Enforce a minimum observation count (configurable, default 100 requests per leg) before committing to a verdict; return Inconclusive if the minimum is not met.
- **Risk**: Per-service AnalysisTemplate configuration drift causes inconsistent analysis behavior. **Mitigation**: Validate templates in CI against a schema; alert on missing templates for services that have enabled canary rollouts.
