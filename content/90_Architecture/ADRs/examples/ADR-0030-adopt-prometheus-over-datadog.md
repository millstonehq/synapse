---
id: ADR-0030
type: adr
title: Adopt Prometheus Over Datadog
status: accepted
owner: Tech Lead
created: '2025-04-12T22:15:10.407Z'
updated: '2026-11-27T00:12:46.984Z'
tags:
  - adr
  - monitoring-stack
summary: Adopt Prometheus Over Datadog
example: true
---

## Context

The engineering organization is growing rapidly and the current monitoring approach — a mix of ad-hoc Datadog dashboards, custom scripts, and manual threshold alerting — is not scaling. Several teams have noted that alert fatigue is increasing due to poorly calibrated thresholds, and there is no consistent observability standard across services. We need to choose a primary metrics platform that will serve as the foundation for the monitoring stack.

Two serious candidates emerged from initial evaluation: Prometheus (open-source, self-hosted) and Datadog (SaaS, fully managed). Both were evaluated over a 6-week trial period. Key evaluation criteria: cost at scale, operational control, integration with existing Kubernetes infrastructure, query language expressiveness, and team expertise availability.

The organization's current infrastructure is Kubernetes-native. All services are instrumented with `/metrics` endpoints exposing Prometheus-format metrics. Adopting Prometheus would require minimal instrumentation changes. Datadog would require either adding a Datadog agent alongside Prometheus exporters or replacing the existing metric endpoints with Datadog's SDK.

## Decision

We will adopt **Prometheus** as the primary metrics collection and alerting platform, with Grafana as the visualization layer and AlertManager for alert routing.

Prometheus will be deployed as a high-availability pair (two instances with identical configs) per environment. Metrics will be forwarded via remote write to the Metrics Collection Service (ScyllaDB-backed) for long-term retention beyond Prometheus's local 15-day TSDB window. Alerting rules will live in the same repository as infrastructure code, reviewed via pull request. All new services must expose a Prometheus-format `/metrics` endpoint with standard labels.

## Consequences

**Positive:**
- Zero incremental cost per metric series — no per-host or per-metric pricing
- Kubernetes-native service discovery requires zero configuration per new service
- PromQL is the de facto standard for metrics querying; hiring pool of engineers familiar with it is large
- Full data ownership — metric data is stored in our infrastructure, not a third-party SaaS

**Negative:**
- Operational burden: we own the Prometheus cluster, storage, and HA configuration
- No built-in anomaly detection or ML-based alerting (must build or integrate separately)
- Scaling Prometheus beyond a single region requires additional components (Thanos, Cortex)

**Neutral:**
- Grafana is the standard open-source visualization companion; switching from Datadog dashboards requires rebuilding dashboards in Grafana (one-time effort estimated at 2 engineer-weeks)

## Alternatives Considered

**Datadog (full SaaS):**
- Pro: Fully managed, built-in anomaly detection, integrated logs/traces/metrics, excellent UX
- Con: At projected scale (100 services, 5M metric series), estimated annual cost of $180,000/year — 8x the cost of self-hosted Prometheus. No data ownership. Vendor lock-in via proprietary query language (DQL).
- Rejected because: Cost at scale is prohibitive, and exporting data from Datadog requires their APIs, creating vendor dependency.

**Victoria Metrics (Prometheus-compatible, self-hosted):**
- Pro: More efficient storage than Prometheus TSDB, lower memory usage at high cardinality
- Con: Less community adoption than Prometheus, fewer engineers familiar with operational runbooks. Prometheus HA pair with remote write is sufficient for our scale.
- Rejected because: Prometheus is the safer choice given hiring pool and community support.
