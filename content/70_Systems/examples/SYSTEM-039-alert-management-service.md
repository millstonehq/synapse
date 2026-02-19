---
id: SYSTEM-039
type: system
title: Alert Management Service
status: review
owner: Monitoring Engineering
owner_team: Monitoring Engineering
runtime: Kubernetes / Node.js 20 / PostgreSQL 16
created: '2025-06-04T03:43:08.524Z'
updated: '2026-01-31T21:33:21.919Z'
tags:
  - system
  - monitoring-stack
summary: Alert Management Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/alert-management-service
dependencies:
  - Log Aggregation Pipeline
  - Metrics Collection Service
runbooks:
  - RUNBOOK-055
  - RUNBOOK-052
example: true
---

## Overview

The Alert Management Service is the central routing and deduplication layer for all operational alerts across the monitoring platform. It receives firing alerts from Prometheus AlertManager, evaluates routing rules to determine the correct notification channel, deduplicates repeated firings within configurable windows, and delivers notifications via PagerDuty, Slack, and email.

The service maintains a complete alert history in PostgreSQL, enabling on-call engineers to review alert patterns, track acknowledgement and resolution times, and generate alert volume reports. It also exposes a REST API for programmatic alert suppression and maintenance window management.

## Architecture

- **Alert Ingestion**: Webhook receiver for AlertManager `v2` alert payloads. Validates signature, deduplicates against active alerts (fingerprint-based), and persists to PostgreSQL.
- **Routing Engine**: Evaluates routing trees (YAML-configured) to determine notification targets. Supports label-based matching, time-of-day overrides, and team ownership rules.
- **Notification Adapters**: PagerDuty (SEV-1/SEV-2), Slack webhooks (all severities), email digest (low-priority). Each adapter retries with exponential backoff.
- **State Management**: Tracks alert lifecycle (firing → acknowledged → resolved). Stores ack metadata (who, when, note) for postmortem context.
- **REST API**: Node.js 20 / Express API for maintenance windows, alert suppression rules, routing config CRUD, and alert history queries.

## Repositories

- [alert-management-service](https://git.example.com/acme/alert-management-service) - Application code, DB migrations, routing config

## Runtime Environment

- **Platform**: Kubernetes, multi-zone
- **Language**: Node.js 20
- **Database**: PostgreSQL 16, primary + 1 read replica, 90-day alert history
- **Replicas**: 3 pods minimum, autoscaling to 8

## Dependencies

- Log Aggregation Pipeline - log-based alert rule evaluation (error log rate)
- Metrics Collection Service - metric threshold alert evaluation

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Alert delivery latency | P99 < 30s from receipt to PagerDuty notification |
| Deduplication accuracy | < 1% false duplicate suppression |
| History retention | 90 days alert history queryable |

## Runbooks

- [[RUNBOOK-055|Alert Routing Failure Runbook]]
- [[RUNBOOK-052|Alert Management Service Recovery Runbook]]
