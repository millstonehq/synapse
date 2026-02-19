---
id: SYSTEM-021
type: system
title: Search Query Processing Service
status: approved
owner: Search Engineering
owner_team: Search Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-08-30T01:34:26.412Z'
updated: '2026-11-25T02:06:46.798Z'
tags:
  - system
  - search-platform
summary: Search Query Processing Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/search-query-processing-service
dependencies:
  - Search Autocomplete Service
  - Search Indexing Pipeline
runbooks:
  - RUNBOOK-029
  - RUNBOOK-033
example: true
---

## Overview

The Search Query Processing Service is the primary entry point for all search requests on the platform. It receives user queries, normalizes and parses them, fans out to the relevant Elasticsearch indices, applies relevance scoring, and returns ranked result sets to callers.

The service handles approximately 12 million queries per day with a peak of 800 QPS during business hours. It supports keyword, phrase, boolean, and hybrid (keyword + vector) query modes, and integrates with the Search Autocomplete Service for inline suggestion enrichment and the Search Indexing Pipeline for index health awareness.

## Architecture

The service follows a pipeline architecture with pluggable stages:

- **Query Parser Layer**: Receives raw query strings, tokenizes, normalizes (lowercasing, diacritic folding), and classifies query intent (navigational, informational, transactional). Outputs a structured query AST.
- **Query Rewrite Layer**: Applies synonym expansion, spell correction, and field-boosting rules from the relevance configuration store in DynamoDB.
- **Fan-out Layer**: Routes the structured query to the appropriate Elasticsearch indices based on content type filters and routing rules. Supports parallel execution across up to 4 index shards.
- **Ranking Layer**: Merges shard results, applies Reciprocal Rank Fusion for hybrid queries, and invokes the Search Relevance Engine for personalized re-ranking when user context is available.
- **Response Layer**: Serializes the ranked result list, applies field masking, and returns paginated results to the caller.

## Repositories

- [search-query-processing-service](https://git.example.com/acme/search-query-processing-service) - Application code, Lambda handlers, DynamoDB schema

## Runtime Environment

- **Platform**: AWS Lambda (Node.js 20) with Provisioned Concurrency to eliminate cold starts
- **Configuration store**: DynamoDB table `search-query-config` for relevance rules and routing config
- **Concurrency**: Up to 500 concurrent Lambda executions; provisioned concurrency set to 50
- **Deployment**: AWS SAM with blue/green alias routing; traffic shifts 10% → 100% over 10 minutes
- **TLS**: All Elasticsearch calls over TLS 1.3; Lambda invocations over VPC private endpoints

## Dependencies

- Elasticsearch 8.x cluster (3 data nodes, 2 coordinating nodes) — primary search backend
- DynamoDB `search-query-config` — relevance rules, synonym lists, routing tables
- Search Relevance Engine — optional re-ranking; called asynchronously, skipped on timeout
- Search Autocomplete Service — inline suggestion enrichment on partial queries

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Latency | P50 < 80ms, P95 < 200ms, P99 < 500ms |
| Error rate | < 0.05% 5xx responses |
| Recovery | MTTR < 15 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-029|Search Query Processing - High Latency Runbook]]
- [[RUNBOOK-033|Search Service On-Call Runbook]]
