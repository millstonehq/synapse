---
id: WIKI-031
type: wiki
title: Grafana - Dashboard Templates
status: approved
owner: Monitoring Team
created: '2025-08-21T09:06:42.856Z'
updated: '2025-10-18T08:36:50.140Z'
tags:
  - wiki
  - monitoring-stack
summary: Grafana - Dashboard Templates
source_repo: https://git.example.com/acme/grafana
commit_sha: a50641a4bd258fa99893b68a9e954f76ea10aca3
generated_at: '2025-09-09T19:40:54.101Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: medium
example: true
---

## Overview

This page documents the standard Grafana dashboard templates used across the monitoring stack. All dashboards are provisioned via the Grafana provisioning pipeline (GitOps — changes to JSON templates in the repo are auto-applied). Dashboard UIDs are stable and referenced in runbooks.

Templates are organized by domain: service-level dashboards (one per service), infrastructure dashboards (Kubernetes, databases), and SLO dashboards (error budget tracking).

## Architecture

Dashboard provisioning uses Grafana's file-based provisioning under `/etc/grafana/provisioning/dashboards/`. A ConfigMap in the `monitoring` namespace is reconciled from the git repository by ArgoCD. Grafana watches the provisioning path and hot-reloads dashboards without restart.

Datasources are also provisioned as code. The primary datasource is Prometheus (pointing to the HA pair via a load-balanced service endpoint). A Loki datasource is configured for the Log Aggregation Pipeline query API.

## Key Components

### Service Dashboard Template

Standard panels on every service dashboard:

- **Request rate**: `sum(rate(http_requests_total{service="$service"}[5m])) by (status_code)` — grouped by HTTP status class
- **Error rate**: `sum(rate(http_requests_total{service="$service",status_code=~"5.."}[5m])) / sum(rate(http_requests_total{service="$service"}[5m]))`
- **P50/P95/P99 latency**: histogram quantile panels with configurable time range
- **Pod restarts**: `increase(kube_pod_container_status_restarts_total{namespace="$namespace"}[1h])`
- **Resource usage**: CPU and memory request/limit utilization per pod

### SLO Dashboard Template

Panels for each service with a defined SLO:

- **Error budget remaining**: percentage of monthly budget not yet consumed
- **Burn rate (1h / 6h)**: current error budget consumption rate vs. thresholds
- **SLO compliance over time**: 28-day rolling compliance chart
- **Recent SLO breaches**: table of breach events with duration and severity

### Infrastructure Dashboards

- **Kubernetes cluster overview**: node CPU/memory/disk, pod counts per namespace, PVC utilization
- **ScyllaDB**: read/write throughput, latency percentiles, compaction lag
- **ClickHouse**: insert rate, query rate, disk usage per table, replication health

## Configuration

| Setting | Value |
|---------|-------|
| Provisioning path | `/etc/grafana/provisioning/dashboards/` |
| Default datasource | Prometheus (HA pair) |
| Dashboard UID prefix | `ms-` for monitoring-stack dashboards |
| Refresh interval | 30s (dashboards), 5m (SLO panels) |

## Dependencies

- Metrics Collection Service - PromQL datasource for all metric panels
- Log Aggregation Pipeline - Loki datasource for log panels and log-metric correlations
- Grafana provisioning pipeline - automated dashboard deployment from git
