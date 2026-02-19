---
id: TDD-039
type: tdd
title: Custom Dashboard Builder TDD
status: approved
owner: Senior Engineer
created: '2024-07-24T05:58:17.272Z'
updated: '2025-03-22T06:23:48.806Z'
tags:
  - tdd
  - monitoring-stack
summary: Custom Dashboard Builder TDD
related_adrs:
  - ADR-0030
  - ADR-0033
example: true
---

## Summary

Design a self-service dashboard builder that allows service teams to create Grafana dashboards without writing raw JSON or PromQL. Teams define dashboards using a structured YAML DSL that describes panels, metrics, and layout; the builder generates valid Grafana dashboard JSON and publishes it to the provisioning pipeline. This eliminates the bottleneck of Monitoring Engineering having to review every new dashboard request.

The builder integrates with the metric catalog established in [[ADR-0030|ADR-0030]] (Prometheus as the metrics platform) and generates SLO panels pre-wired to the error budget visualization format from [[ADR-0033|ADR-0033]].

## Overview

- **YAML DSL**: A declarative dashboard definition format. Teams specify panel type (timeseries, stat, table), metric expression (PromQL or a pre-defined template), title, and thresholds. No JSON required.
- **Metric catalog integration**: The DSL supports `template:` references (e.g., `template: error_rate`) that expand to the correct PromQL expression for the service, reducing copy-paste errors.
- **Validation**: The builder validates that referenced metrics exist in the Metrics Collection Service catalog before generating Grafana JSON. Invalid metrics fail at build time, not at dashboard render time.
- **GitOps publishing**: Generated Grafana JSON is committed to the provisioning repo via the builder's CI integration. Dashboards go live automatically when the PR is merged.

## Architecture

- **DSL parser**: Reads YAML dashboard definitions and validates against the dashboard schema (JSON Schema). Reports clear errors for malformed definitions.
- **Template engine**: Expands `template:` references by looking up the metric catalog (a versioned YAML catalog of standard metric names and their PromQL expressions). Team-provided overrides can extend the catalog per-service.
- **PromQL validator**: Sends the expanded PromQL expression to the Prometheus API (`/api/v1/query` with a point-in-time query) to validate it returns data before including it in the dashboard.
- **Grafana JSON generator**: Translates the validated DSL into Grafana dashboard JSON. Supports timeseries, stat, bar gauge, table, and log panel types.
- **Publishing CLI**: A `dashboard-builder publish` command that generates JSON and opens a PR to the Grafana provisioning repo.

## Information Model

- **DashboardDef**: `service`, `title`, `uid`, `rows` (list of Row), `variables` (template variables)
- **Row**: `title`, `panels` (list of Panel)
- **Panel**: `type`, `title`, `metric` (PromQL or template ref), `unit`, `thresholds`, `width`
- **MetricTemplate**: `name`, `description`, `promql_template` (with `$service` variable), `default_unit`

## Interfaces

- `dashboard-builder validate <file>` — validate dashboard YAML against schema
- `dashboard-builder build <file> --output <path>` — generate Grafana JSON
- `dashboard-builder publish <file>` — generate JSON and open PR to provisioning repo
- Prometheus API: `GET /api/v1/query` — PromQL validation
- GitHub API: create branch, commit, open PR for provisioning repo

## Files and Layout

```
cmd/dashboard-builder/main.go
internal/
  dsl/                       - YAML parser, schema validation
  templates/                 - Metric template catalog and expansion
  validator/                 - PromQL validation against Prometheus
  generator/                 - Grafana JSON generation
  publisher/                 - Git/GitHub PR integration
catalog/
  metric-templates.yaml      - Standard metric template definitions
examples/
  service-dashboard.yaml     - Example dashboard definition
```

## Work Plan

1. **Phase 1 (Week 1-2)**: DSL schema definition, YAML parser, basic Grafana JSON generator for timeseries panels
2. **Phase 2 (Week 3)**: Metric template catalog, template expansion, remaining panel types
3. **Phase 3 (Week 4)**: PromQL validation integration, clear error messages for invalid expressions
4. **Phase 4 (Week 5)**: GitHub publishing integration, CI pipeline for dashboard validation on PR
5. **Phase 5 (Week 6)**: Migrate 10 existing dashboards to YAML DSL as validation; publish builder docs and runbook

## Risks and Mitigations

- **Risk**: Generated Grafana JSON diverges from Grafana API version, causing provisioning failures. **Mitigation**: Pin to Grafana API version in the generator; validate output against a running Grafana instance in integration tests.
- **Risk**: Metric template catalog becomes stale as services evolve metric names. **Mitigation**: Templates include a `deprecated_at` field; the builder warns (not fails) on deprecated template usage.
- **Risk**: Teams bypass the builder and hand-edit Grafana JSON directly. **Mitigation**: Provisioning repo PR checks validate that all dashboard JSON files have a corresponding YAML source; hand-edited JSON files fail CI.
