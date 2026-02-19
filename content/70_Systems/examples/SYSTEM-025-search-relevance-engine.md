---
id: SYSTEM-025
type: system
title: Search Relevance Engine
status: approved
owner: Search Engineering
owner_team: Search Engineering
runtime: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache
created: '2025-01-30T11:56:03.777Z'
updated: '2026-09-13T15:55:59.973Z'
tags:
  - system
  - search-platform
summary: Search Relevance Engine
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/search-relevance-engine
dependencies:
  - Search Indexing Pipeline
  - Search Query Processing Service
runbooks:
  - RUNBOOK-033
  - RUNBOOK-035
example: true
---

## Overview

The Search Relevance Engine is the machine-learning–backed re-ranking service for the search platform. It consumes a candidate result set from the Search Query Processing Service, applies a learned-to-rank model trained on historical click and dwell-time signals, and returns a re-ranked result list.

The engine is an optional but high-impact component in the query path: when available, it improves NDCG@10 by approximately 12% over the base Elasticsearch BM25 ranking. It is called synchronously with a 30ms timeout; if it does not respond in time, the query layer proceeds with the baseline Elasticsearch ranking.

## Architecture

- **Re-ranking API**: REST endpoint accepting a ranked candidate list (up to 100 results) plus query context. Returns re-ranked list with relevance score explanations.
- **Feature Extractor**: Computes per-(query, result) features: BM25 score, position in original ranking, CTR from the signal store, content recency, user-query affinity (if user context provided).
- **Scoring Model**: LightGBM model loaded at startup from S3 model registry. Produces a relevance score for each candidate. Model is updated weekly via offline training pipeline.
- **Model Loader**: Background thread that polls S3 for new model versions every 5 minutes. Performs atomic hot-swap of the in-memory model without restarting the service.
- **Signal Client**: Reads click-frequency and CTR features from Aurora PostgreSQL `relevance_signals` table (refreshed by Search Analytics Collector).

## Repositories

- [search-relevance-engine](https://git.example.com/acme/search-relevance-engine) - ECS service, Java 21 app, model training scripts, Aurora schema

## Runtime Environment

- **Platform**: ECS Fargate, 6 task replicas, autoscaling on CPU utilization (target 60%)
- **Language**: Java 21 (Spring Boot 3)
- **Signal store**: Aurora PostgreSQL (writer + 1 read replica) — `relevance_signals` table
- **Feature cache**: ElastiCache Redis 7 — per-(query, document) feature cache, 1h TTL
- **Model store**: S3 `search-models-prod` bucket — LightGBM model artifacts
- **Deployment**: ECS rolling update via CodeDeploy; canary 10% → 100% over 15 minutes

## Dependencies

- Aurora PostgreSQL — relevance signal store (CTR, dwell time per query/result pair)
- ElastiCache Redis 7 — feature cache for low-latency scoring
- S3 model registry — LightGBM model artifacts
- Search Indexing Pipeline — triggers signal refresh on reindex completion
- Search Query Processing Service — primary caller; 30ms timeout enforced

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Latency | P50 < 15ms, P95 < 30ms (timeout budget) |
| Model freshness | Updated model deployed within 2 hours of training completion |
| Error rate | < 0.1% 5xx; graceful degradation on timeout |

## Runbooks

- [[RUNBOOK-033|Search Service On-Call Runbook]]
- [[RUNBOOK-035|Search Relevance Engine Degraded Runbook]]
