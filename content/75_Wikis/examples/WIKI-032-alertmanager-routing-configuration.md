---
id: WIKI-032
type: wiki
title: AlertManager - Routing Configuration
status: review
owner: Monitoring Team
created: '2025-07-03T11:55:40.195Z'
updated: '2026-12-21T23:27:49.357Z'
tags:
  - wiki
  - monitoring-stack
summary: AlertManager - Routing Configuration
source_repo: https://git.example.com/acme/alertmanager
commit_sha: ec88ed0850f9c09958607185fdf0b764c7cb0f16
generated_at: '2026-07-21T23:55:26.146Z'
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

This page documents how AlertManager routes alerts to the correct team and notification channel. AlertManager sits downstream of Prometheus and upstream of the Alert Management Service webhook receiver. It handles deduplication (suppressing repeated firings within a `group_wait`), grouping (batching related alerts into single notifications), and routing (choosing receiver based on label matchers).

The routing tree is defined in `alertmanager/config.yml` and is provisioned via ArgoCD. Changes to the routing config require a PR review from a senior SRE before merging.

## Architecture

AlertManager runs as a 3-replica StatefulSet in the `monitoring` namespace. Replicas form a gossip cluster using the `--cluster.peer` flags, ensuring all replicas see all silence and inhibition state. The Prometheus HA pair sends alerts to an AlertManager service (load-balanced across all three replicas).

The webhook integration with the Alert Management Service is configured as a receiver named `alert-management-webhook`. This is the downstream sink for all routed alerts and is responsible for persistence, enrichment, and PagerDuty/Slack delivery.

## Key Components

### Routing Tree

Top-level `route` settings:
- `group_by: [alertname, cluster, service]` - groups alerts by these labels
- `group_wait: 30s` - wait before sending first notification for a new group
- `group_interval: 5m` - minimum time between notifications for the same group
- `repeat_interval: 4h` - resend notification if alert is still firing after this

Sub-routes (matched top-to-bottom):
- `severity=critical, team=*` → `pagerduty-high-urgency` + `alert-management-webhook`
- `severity=warning, team=infra` → `slack-infra-alerts` + `alert-management-webhook`
- `severity=warning` (catch-all) → `slack-warnings` + `alert-management-webhook`
- Default → `alert-management-webhook` only

### Inhibition Rules

- Inhibit `severity=warning` alerts when a `severity=critical` alert fires for the same `service` label — prevents noise during major incidents
- Inhibit all alerts for a service when `maintenance_window=true` label is present on any active alert for that service

### Silence Management

Silences are managed via the AlertManager API (accessible from Grafana) and the Alert Management Service maintenance window feature. Silences created via the Alert Management Service are pushed to AlertManager via its REST API.

## Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Replicas | 3 | Gossip-based HA |
| Gossip port | 9094 | Internal cluster communication |
| API port | 9093 | External alertmanager API |
| Config reload | Hot (SIGHUP) | No restart needed |

## Dependencies

- Alert Management Service - downstream webhook receiver for all routed alerts
- Prometheus HA pair - upstream alert sources
- PagerDuty - direct critical alert receiver (also relayed via Alert Management Service)
