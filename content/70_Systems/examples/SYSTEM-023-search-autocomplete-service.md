---
id: SYSTEM-023
type: system
title: Search Autocomplete Service
status: approved
owner: Search Engineering
owner_team: Search Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-02-21T01:36:26.722Z'
updated: '2026-07-15T03:26:18.817Z'
tags:
  - system
  - search-platform
summary: Search Autocomplete Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/search-autocomplete-service
dependencies:
  - Search Analytics Collector
  - Search Indexing Pipeline
runbooks:
  - RUNBOOK-032
  - RUNBOOK-033
example: true
---

## Overview

The Search Autocomplete Service provides real-time query suggestions as users type in the search box. It serves prefix-based completions from a pre-built suggestion index populated by the Search Indexing Pipeline, enriched with click-frequency signals from the Search Analytics Collector.

The service handles up to 2,000 requests per second at peak and must respond within 50ms P99 to keep the typeahead experience snappy. Suggestions are ranked by a combination of popularity (click-through frequency), recency (recently searched terms), and semantic similarity to the current partial query.

## Architecture

The service is deployed as an AWS Lambda function behind API Gateway:

- **Prefix Matcher**: Performs a prefix query against the DynamoDB `search-suggestions` table. Returns up to 20 raw candidates per prefix.
- **Ranker**: Applies a scoring formula combining term frequency, click-through rate (from the analytics signal table), and recency decay. Returns top 8 candidates.
- **Personalization Layer**: If a user context token is provided, boosts suggestions from the user's recent search history (stored in DynamoDB per-user TTL table).
- **Response Formatter**: Applies highlight markup to the matched prefix, applies content-type category labels, and serializes the response.

The suggestion index is rebuilt incrementally by the Search Indexing Pipeline on each document mutation and fully rebuilt weekly via a batch job.

## Repositories

- [search-autocomplete-service](https://git.example.com/acme/search-autocomplete-service) - Lambda function code, DynamoDB schema, suggestion index rebuild scripts

## Runtime Environment

- **Platform**: AWS Lambda (Node.js 20), Provisioned Concurrency 100 to eliminate cold starts
- **Data store**: DynamoDB `search-suggestions` table (Global Secondary Index on prefix hash), `search-user-history` table (TTL 30 days)
- **Deployment**: AWS SAM with canary alias; 5% → 100% traffic shift over 5 minutes
- **Latency budget**: 50ms P99 end-to-end from API Gateway to response

## Dependencies

- DynamoDB `search-suggestions` — primary suggestion data store, refreshed by Search Indexing Pipeline
- DynamoDB `search-user-history` — per-user recent query history from Search Analytics Collector
- Search Analytics Collector — provides click-frequency and query-frequency signals for ranking

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Latency | P50 < 20ms, P99 < 50ms |
| Suggestion freshness | New documents searchable in suggestions within 5 minutes |
| Error rate | < 0.01% 5xx responses |

## Runbooks

- [[RUNBOOK-032|Search Index Writer Errors Runbook]]
- [[RUNBOOK-033|Search Service On-Call Runbook]]
