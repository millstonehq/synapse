---
id: SYSTEM-040
type: system
title: Status Page Service
status: approved
owner: Monitoring Engineering
owner_team: Monitoring Engineering
runtime: Kubernetes / TypeScript / PostgreSQL 16 / Redis 7
created: '2025-10-19T09:50:27.840Z'
updated: '2025-02-13T14:33:34.713Z'
tags:
  - system
  - monitoring-stack
summary: Status Page Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/status-page-service
dependencies:
  - Distributed Tracing Platform
  - Metrics Collection Service
runbooks:
  - RUNBOOK-053
  - RUNBOOK-050
example: true
---

## Overview

The Status Page Service provides a public-facing and internal dashboard showing the real-time health of all platform services. It aggregates availability signals from the Metrics Collection Service and incident reports from on-call engineers to produce per-service status indicators (operational, degraded, partial outage, major outage). Historical uptime data is shown for the trailing 90 days.

The service is designed to remain available even during major incidents — it is intentionally isolated from the rest of the monitoring stack with its own database and cache, and it serves a statically-rendered fallback page during backend failures.

## Architecture

- **Signal Aggregation**: Polls the Metrics Collection Service every 30 seconds for availability metrics per service. Derives status from SLO burn rate and error rate thresholds. Caches results in Redis 7 for sub-second page loads.
- **Incident Management API**: REST API (TypeScript / Fastify) for engineers to open, update, and resolve incidents. Incident records are persisted in PostgreSQL 16.
- **Public Frontend**: Server-side rendered TypeScript/Next.js application. Serves static fallback from CDN edge if the backend is unreachable.
- **Subscriber Notifications**: Email and webhook subscriptions for status change events. Delivers within 60 seconds of a status transition.
- **Historical Uptime**: Computes per-service monthly and quarterly uptime percentages from the availability metric history.

## Repositories

- [status-page-service](https://git.example.com/acme/status-page-service) - Application code, DB migrations, CDN config

## Runtime Environment

- **Platform**: Kubernetes, multi-zone + CDN edge for static fallback
- **Language**: TypeScript (Node.js 20)
- **Database**: PostgreSQL 16, primary + 1 read replica
- **Cache**: Redis 7, 2-node cluster
- **Replicas**: 3 pods minimum

## Dependencies

- Distributed Tracing Platform - trace-linked incident context in status updates
- Metrics Collection Service - availability metric polling for status computation

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Status update latency | < 60s from metric change to page update |
| Page load (P95) | < 800ms globally via CDN |
| Incident notification | < 60s from incident creation to subscriber email |

## Runbooks

- [[RUNBOOK-053|Status Page Outage Runbook]]
- [[RUNBOOK-050|Status Page Subscriber Notification Failure Runbook]]
