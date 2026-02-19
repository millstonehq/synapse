---
id: SYSTEM-045
type: system
title: Customer Analytics Service
status: deprecated
owner: Customer Engineering
owner_team: Customer Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2024-12-11T14:01:49.702Z'
updated: '2026-09-09T12:41:06.875Z'
tags:
  - system
  - customer-portal
summary: Customer Analytics Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/customer-analytics-service
dependencies:
  - Customer Support Widget Service
  - Customer Preference Service
runbooks:
  - RUNBOOK-062
  - RUNBOOK-061
example: true
---

## Overview

The Customer Analytics Service collects and processes behavioral event data from the Customer Portal to power dashboards, funnel analysis, retention reporting, and feature usage metrics. It ingests events from the Customer Support Widget Service and Customer Preference Service, enriches them, and exposes aggregated metrics via an internal query API.

The service runs on ECS Fargate / Python 3.12 / OpenSearch / Redis 7 and is currently in deprecated status, with migration to a new analytics platform underway. It targets 99.99% monthly uptime.

## Architecture

- **Event Ingestion**: Receives events via an internal REST endpoint. Events are validated, enriched with customer segment metadata, and written to OpenSearch.
- **Query API**: Authenticated REST API for querying aggregated metrics (daily active users, feature adoption rates, support ticket conversion funnels). Results cached in Redis 7 with a 15-minute TTL.
- **Retention Pipeline**: Nightly batch job (ECS Fargate scheduled task) computes cohort retention tables and writes results to OpenSearch for dashboard queries.
- **Alerting**: Monitors event ingestion lag. If ingest falls more than 5 minutes behind, a CloudWatch alarm pages the on-call team.

## Repositories

- [customer-analytics-service](https://git.example.com/acme/customer-analytics-service) - Service code, Fargate task definitions

## Runtime Environment

- **Platform**: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
- **Deployment**: ECS rolling update with minimum 50% healthy tasks during deploy
- **Scaling**: Fargate task count autoscales 2-8 based on event queue depth

## Dependencies

- Customer Support Widget Service - widget interaction events (ticket creation, chat sessions, FAQ clicks)
- Customer Preference Service - preference change events for feature adoption analysis
- OpenSearch - event storage and aggregation queries
- Redis 7 - query result cache

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Event ingest lag | < 5 minutes P95 |
| Query API P95 | < 500ms (cache hit) |
| Recovery | MTTR < 15 minutes for SEV-1 |

## Runbooks

- [[RUNBOOK-079|Customer Portal SSL Certificate Runbook]]
