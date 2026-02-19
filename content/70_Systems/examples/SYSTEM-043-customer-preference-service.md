---
id: SYSTEM-043
type: system
title: Customer Preference Service
status: draft
owner: Customer Engineering
owner_team: Customer Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2025-01-12T13:19:25.524Z'
updated: '2025-04-03T07:11:53.896Z'
tags:
  - system
  - customer-portal
summary: Customer Preference Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/customer-preference-service
dependencies:
  - Customer Analytics Service
  - Customer API Gateway
runbooks:
  - RUNBOOK-079
  - RUNBOOK-060
example: true
---

## Overview

The Customer Preference Service stores and serves per-customer configuration data including notification settings, display preferences, language and timezone, communication opt-ins, and dashboard layout customizations. It is a read-heavy service with write operations triggered by user actions in the portal settings UI.

The service is consumed by the Customer API Gateway and feeds preference data to the Customer Analytics Service for behavioral analysis. It runs on Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13 and targets 99.9% monthly uptime.

## Architecture

- **REST API Layer**: CRUD endpoints for preference namespaces (notifications, display, communications). All mutations require authenticated user context; reads can be served from cache.
- **Preference Model**: Preferences are stored as typed key-value pairs within named namespaces. Schema is validated against a JSON Schema registry to prevent invalid preference values.
- **Caching Layer**: Redis TTL cache (5 min) for preference reads. Cache is invalidated on write via RabbitMQ event publishing.
- **Event Publishing**: Preference change events published to RabbitMQ for downstream consumers (Customer Analytics Service) to react to user setting changes.
- **Data Layer**: PostgreSQL 16 with a single `preferences` table partitioned by `customer_id` hash for read scalability.

## Repositories

- [customer-preference-service](https://git.example.com/acme/customer-preference-service) - Service code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
- **Replicas**: 2 pods minimum, autoscaling to 6 on request rate
- **Deployment**: Rolling deploy via ArgoCD
- **Config**: Environment variables via Kubernetes ConfigMaps; DB credentials rotated every 90 days

## Dependencies

- Customer Analytics Service - consumes preference change events
- Customer API Gateway - primary caller for preference reads and writes
- Redis - preference read cache
- RabbitMQ - event bus for preference change notifications

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| P95 read latency | < 50ms (cache hit) / < 150ms (DB) |
| Error rate | < 0.1% 5xx responses |
| Recovery | MTTR < 30 minutes for SEV-1 |

## Runbooks

- [[RUNBOOK-079|Customer Portal SSL Certificate Runbook]]
