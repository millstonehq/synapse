---
id: SYSTEM-024
type: system
title: Search Analytics Collector
status: accepted
owner: Search Engineering
owner_team: Search Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2024-03-18T16:46:16.966Z'
updated: '2025-12-10T03:48:12.270Z'
tags:
  - system
  - search-platform
summary: Search Analytics Collector
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/search-analytics-collector
dependencies:
  - Search Relevance Engine
  - Search Autocomplete Service
runbooks:
  - RUNBOOK-033
  - RUNBOOK-031
example: true
---

## Overview

The Search Analytics Collector receives, processes, and stores search interaction events — including queries issued, results displayed, and result clicks — for use by the relevance and autocomplete systems and for product analytics dashboards.

The service ingests approximately 15 million events per day via a Kinesis data stream. It computes real-time aggregates (click-through rate per query/result pair, zero-result rate by query term) and writes them to OpenSearch for dashboards and to Redis for low-latency consumption by the autocomplete ranking layer.

## Architecture

- **Event Receiver**: HTTP endpoint that accepts batched click and query impression events from frontend clients. Validates event schema, assigns server-side timestamps, and publishes to Kinesis `search-events` stream.
- **Stream Processor**: ECS Fargate consumers that read from Kinesis, normalize and deduplicate events, and fan out to two sinks: OpenSearch (full event storage) and Redis (real-time aggregation counters).
- **Aggregation Job**: Scheduled Python job (runs every 5 minutes) that computes rolling 24h CTR per (query, result_id) pair and writes to the `search-signals` table in Redis.
- **Signal Publisher**: Pushes updated click-frequency signals to Search Autocomplete Service and trigger notifications to Search Relevance Engine for relevance model refresh.

## Repositories

- [search-analytics-collector](https://git.example.com/acme/search-analytics-collector) - ECS task definitions, Python consumers, OpenSearch index templates

## Runtime Environment

- **Platform**: ECS Fargate, 4 task replicas for stream processors, autoscaling on Kinesis shard lag
- **Language**: Python 3.12
- **Event stream**: Kinesis Data Streams, 4 shards, 7-day retention
- **Analytics store**: OpenSearch 2.x cluster, 3 data nodes, 30-day hot retention
- **Signal cache**: Redis 7 Cluster (3 nodes), `search-signals` hash keys with 48h TTL
- **Deployment**: ECS rolling update via CodeDeploy; no-downtime stream processor swap

## Dependencies

- Kinesis Data Streams — event ingestion transport
- OpenSearch 2.x — full event storage and dashboard backend
- Redis 7 — real-time CTR aggregation and signal cache for autocomplete
- Search Relevance Engine — receives signal-refresh notifications
- Search Autocomplete Service — consumes click-frequency signals from Redis

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Event processing lag | P95 < 60 seconds from event receipt to OpenSearch |
| Signal refresh latency | Rolling CTR updated within 5 minutes |
| Error rate | < 0.1% event drops (excluding malformed events) |

## Runbooks

- [[RUNBOOK-033|Search Service On-Call Runbook]]
- [[RUNBOOK-031|Search Indexing Pipeline Backlog Runbook]]
