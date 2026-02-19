---
id: WIKI-030
type: wiki
title: Prometheus - Cluster Configuration
status: approved
owner: Monitoring Team
created: '2024-07-06T05:15:54.022Z'
updated: '2026-06-17T20:36:47.641Z'
tags:
  - wiki
  - monitoring-stack
summary: Prometheus - Cluster Configuration
source_repo: https://git.example.com/acme/prometheus
commit_sha: 6aa9c764186f9aa02d2c43765be791084df88346
generated_at: '2026-05-06T02:30:51.250Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: medium
example: true
---

## Overview

This page documents the Prometheus cluster configuration used by the monitoring stack. We run two Prometheus instances in a high-availability pair per environment (production, staging) with a shared AlertManager cluster. Remote write is configured to forward all scraped metrics to the Metrics Collection Service (ScyllaDB-backed) for long-term retention beyond Prometheus's local 15-day TSDB window.

## Architecture

The production Prometheus setup:

- **Prometheus HA pair**: Two Prometheus instances (`prometheus-0` and `prometheus-1`) in the `monitoring` namespace, each scraping all targets independently. Identical configuration ensures consistent series.
- **AlertManager cluster**: Three AlertManager replicas using gossip-based deduplication (`cluster.peer` config). Alerts from either Prometheus instance reach all AlertManagers but fire only once.
- **Remote write**: Both Prometheus instances write to the Metrics Collection Service remote write endpoint at `http://metrics-collection-svc:9090/api/v1/write`. Queuing is enabled with `max_samples_per_send: 10000` and `capacity: 50000` to absorb backend slowdowns.
- **Thanos Sidecar** (optional): A Thanos sidecar on each Prometheus pod uploads 2-hour TSDB blocks to object storage for cross-cluster querying.

## Key Components

### Scrape Configuration

Scrape configs are split into files under `scrape_configs/` and loaded via `file_sd_configs` from Kubernetes pod annotations. Key scrape jobs:

- `kubernetes-pods`: Scrapes all pods with `prometheus.io/scrape: "true"` annotation. 30s interval.
- `kubernetes-nodes`: Scrapes node-exporter on each node for CPU, memory, disk, network metrics. 15s interval.
- `kubernetes-apiservers`: Scrapes kube-apiserver metrics for cluster health. 60s interval.
- `monitoring-stack`: Scrapes all monitoring-stack components at 15s interval for self-monitoring.

### Recording Rules

Pre-computed aggregations to reduce query latency on Grafana dashboards:

- `job:request_rate5m` - per-job HTTP request rate over 5m
- `job:error_rate5m` - per-job 5xx error rate over 5m
- `instance:cpu_usage_rate5m` - per-instance CPU usage rate

### AlertManager Routing

AlertManager routes are defined in `alertmanager/config.yml`. Top-level receiver is `default-pagerduty`. Sub-routes:
- `severity=critical` → PagerDuty high-urgency
- `severity=warning` → Slack `#alerts-warning`
- `team=infra` → Slack `#infra-alerts` and PagerDuty infra rotation

## Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Retention | 15 days | Local TSDB; 90 days via remote write |
| Scrape interval | 30s (default) | Override per job |
| Evaluation interval | 30s | Alert rule evaluation |
| Remote write timeout | 30s | Per request to Metrics Collection Service |

## Dependencies

- Metrics Collection Service - remote write target for long-term metric storage
- AlertManager cluster - alert routing and deduplication
- Node Exporter DaemonSet - host-level metrics
- kube-state-metrics - Kubernetes object state metrics
