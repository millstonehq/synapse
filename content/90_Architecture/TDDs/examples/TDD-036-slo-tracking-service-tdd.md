---
id: TDD-036
type: tdd
title: SLO Tracking Service TDD
status: approved
owner: Senior Engineer
created: '2025-07-04T02:03:23.475Z'
updated: '2025-04-30T11:22:08.954Z'
tags:
  - tdd
  - monitoring-stack
summary: SLO Tracking Service TDD
related_adrs:
  - ADR-0030
  - ADR-0033
example: true
---

## Summary

Design a service that continuously tracks SLO compliance for all platform services, computes error budget consumption rates, and exposes SLO state via a REST API for dashboards and alerting integrations. The service must support 99.9%, 99.95%, and 99.99% SLO targets and handle multi-window burn rate calculations as specified in [[ADR-0033|ADR-0033]].

The SLO Tracking Service reads availability metrics from the Prometheus-compatible metrics layer (as established in [[ADR-0030|ADR-0030]]) and computes error budget state on a configurable evaluation cadence. It stores SLO compliance history in its own database for quarterly reporting and postmortem context.

## Overview

- **SLO definitions are code**: Service SLO configurations (target, window, indicator metric) are stored in version-controlled YAML files and loaded at startup. Adding a new SLO requires a PR, not a UI click.
- **Burn rate computation**: The service computes 1-hour, 6-hour, and 24-hour burn rates for each SLO on every evaluation cycle (every 30 seconds).
- **History persistence**: Compliance state is written to TimescaleDB (PostgreSQL extension) for efficient time-range queries on historical SLO data.
- **Alert integration**: The service exposes a webhook that AlertManager can call to query current burn rates, enabling dynamic alert thresholds rather than PromQL-only rules.

## Architecture

- **Config loader**: Reads SLO definition YAML from a mounted ConfigMap; validates and reloads on SIGHUP without restart.
- **Metrics fetcher**: Queries the Prometheus API (HTTP) for the current error rate metric for each SLO definition. Caches responses for 15 seconds to avoid hammering Prometheus.
- **Burn rate calculator**: Computes remaining error budget and burn rates at 1h/6h/24h windows using the formulas defined in ADR-0033.
- **State store**: TimescaleDB hypertable `slo_evaluations(service, slo_name, timestamp, remaining_budget_pct, burn_rate_1h, burn_rate_6h)`. Hypertable partitioned by day.
- **REST API**: Exposes `/api/v1/slos` (list all SLOs with current state) and `/api/v1/slos/{service}` (SLO state for a service). Used by Grafana SLO dashboard panels.

## Information Model

- **SLODefinition**: `service_name`, `slo_name`, `target_pct` (e.g., 99.9), `window_days` (30), `indicator_metric` (PromQL expression), `owner_team`
- **SLOEvaluation**: `service_name`, `slo_name`, `timestamp`, `remaining_budget_pct`, `burn_rate_1h`, `burn_rate_6h`, `burn_rate_24h`, `status` (healthy/at-risk/breached)
- **SLOBreach**: `service_name`, `slo_name`, `breach_start`, `breach_end`, `budget_consumed_pct`

## Interfaces

- `GET /api/v1/slos` — list all SLOs with current state and remaining budget
- `GET /api/v1/slos/{service}` — SLO details for a specific service
- `GET /api/v1/slos/{service}/history?from=&to=` — historical compliance for time range
- `POST /api/v1/webhook/burn-rate` — AlertManager webhook endpoint for querying current burn rate (for dynamic alert routing)
- Internal: Prometheus HTTP API client for metric queries

## Files and Layout

```
cmd/slo-tracker/main.go      - Entry point, dependency injection
internal/
  config/                    - SLO definition loader, YAML parser
  fetcher/                   - Prometheus API client
  calculator/                - Burn rate computation logic
  store/                     - TimescaleDB repository
  api/                       - REST API handlers
slo-definitions/             - YAML SLO definition files (one per service)
deploy/
  helm/                      - Kubernetes Helm chart
  migrations/                - TimescaleDB migrations
```

## Work Plan

1. **Phase 1 (Week 1-2)**: TimescaleDB schema, SLO config YAML loader, basic evaluation loop
2. **Phase 2 (Week 3)**: Prometheus metrics fetcher, burn rate calculator implementation, unit tests
3. **Phase 3 (Week 4)**: REST API, Grafana SLO dashboard integration, alerting webhook
4. **Phase 4 (Week 5)**: Load test (100 SLOs, 30s eval cycle), performance tuning, production deployment

## Risks and Mitigations

- **Risk**: Prometheus API rate limits under high SLO count. **Mitigation**: Batch Prometheus queries using multi-query endpoint; cache responses for 15s.
- **Risk**: TimescaleDB disk growth from frequent evaluations. **Mitigation**: Compress evaluations older than 7 days using TimescaleDB compression; purge after 1 year.
- **Risk**: SLO definition changes during an evaluation cycle. **Mitigation**: SIGHUP-triggered config reload is atomic; in-flight evaluations complete before reload applies.
