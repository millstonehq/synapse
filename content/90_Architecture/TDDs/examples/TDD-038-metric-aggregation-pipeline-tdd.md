---
id: TDD-038
type: tdd
title: Metric Aggregation Pipeline TDD
status: approved
owner: Principal Engineer
created: '2025-04-21T13:10:30.043Z'
updated: '2025-06-17T04:38:22.569Z'
tags:
  - tdd
  - monitoring-stack
summary: Metric Aggregation Pipeline TDD
related_adrs:
  - ADR-0030
  - ADR-0033
example: true
---

## Summary

Design a batch metric aggregation pipeline that pre-computes recording rules, downsampled time-series, and SLO compliance summaries on a scheduled basis. This pipeline complements the real-time query path by maintaining a set of pre-aggregated metrics that dramatically reduce Grafana dashboard query times and network egress costs (as identified in REPORT-063).

The pipeline is downstream of the Metrics Collection Service (built on [[ADR-0030|ADR-0030]]-standardized Prometheus) and produces outputs consumed by the error budget alerting system described in [[ADR-0033|ADR-0033]].

## Overview

- **Recording rule evaluation**: Executes a catalog of PromQL recording rules against the Metrics Collection Service on a 30-second cadence and writes results back as new metric series. Eliminates expensive fan-out queries from Grafana dashboards.
- **Downsampling**: Creates 5-minute, 1-hour, and 1-day resolution downsample series for all metrics, retaining min/max/avg/count aggregations. Enables fast queries over long time ranges (30-day or 90-day windows) without scanning full-resolution data.
- **SLO rollup computation**: Computes per-service hourly availability percentages and writes them as summary metrics for the SLO Tracking Service to consume instead of querying raw event data.

## Architecture

- **Rule catalog**: YAML-defined recording rules, versioned in git and loaded by the pipeline at startup. Rules are hot-reloaded via SIGHUP.
- **Evaluation engine**: A Rust-based PromQL evaluation engine that queries the Metrics Collection Service remote read API, applies each rule, and writes results back via remote write.
- **Downsampling worker**: Separate worker pool that runs downsampling passes for all active metric series at the end of each 5-minute window. Uses ScyllaDB's batch write API for efficiency.
- **SLO rollup worker**: Reads per-service error rate metrics and computes hourly availability; writes to the `slo_availability_hourly` Prometheus metric series.
- **Scheduler**: Cron-based job scheduler with jitter to avoid thundering herd when many rules evaluate simultaneously.

## Information Model

- **RecordingRule**: `name`, `expr` (PromQL), `interval`, `labels` (additional labels to attach to output series)
- **DownsampleConfig**: `metric_pattern`, `resolutions` (5m/1h/1d), `aggregations` (min/max/avg/count)
- **SLORollupResult**: `service`, `hour`, `total_requests`, `error_requests`, `availability_pct`

## Interfaces

- Metrics Collection Service remote read API — input source for all evaluations
- Metrics Collection Service remote write API — output sink for recording rule results and downsample series
- `GET /api/v1/rules` — list active recording rules and their last evaluation status
- `POST /api/v1/rules/reload` — trigger hot reload of rule catalog from ConfigMap

## Files and Layout

```
cmd/aggregation-pipeline/main.go
internal/
  catalog/                   - Recording rule and downsampling config loader
  engine/                    - PromQL evaluation engine (Prometheus library wrapper)
  downsample/                - Time-series downsampling worker
  slorollup/                 - SLO availability rollup computation
  scheduler/                 - Cron-based job scheduler with jitter
  metricsio/                 - Prometheus remote read/write clients
```

## Work Plan

1. **Phase 1 (Week 1-2)**: Rule catalog loader, Prometheus remote read/write clients, basic evaluation loop for recording rules
2. **Phase 2 (Week 3)**: Downsampling worker with 5m/1h/1d resolutions; integration tests against Metrics Collection Service staging instance
3. **Phase 3 (Week 4)**: SLO rollup worker; validate outputs consumed by SLO Tracking Service
4. **Phase 4 (Week 5)**: Performance test at 1000 rules, 10M active series; tuning scheduler jitter and batch sizes
5. **Phase 5 (Week 6)**: Production deployment; validate dashboard query time improvements

## Risks and Mitigations

- **Risk**: Recording rule evaluation loop falls behind if Metrics Collection Service is slow. **Mitigation**: Evaluation intervals are independent per rule; a slow rule does not block others. Alert on evaluation lag > 2x interval.
- **Risk**: Downsampled series accumulate and consume excessive storage. **Mitigation**: Downsampled series are stored with explicit retention labels; the Metrics Collection Service applies shorter retention (60 days) to downsampled series.
- **Risk**: Wrong recording rule results are silently written (PromQL expression bugs). **Mitigation**: All recording rules must pass a unit test (using `promtool test rules`) in CI before merging to the rule catalog.
