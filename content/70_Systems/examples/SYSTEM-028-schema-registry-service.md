---
id: SYSTEM-028
type: system
title: Schema Registry Service
status: approved
owner: Data Engineering
owner_team: Data Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-08-19T00:36:41.998Z'
updated: '2026-12-25T03:46:14.021Z'
tags:
  - system
  - data-pipeline
summary: Schema Registry Service
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/schema-registry-service
dependencies:
  - Data Quality Monitor
  - Event Streaming Platform
runbooks:
  - RUNBOOK-042
  - RUNBOOK-037
example: true
---

## Overview

The Schema Registry Service stores, versions, and enforces Avro schemas used by all data pipeline producers and consumers. It provides a REST API for schema registration, compatibility checking, and schema retrieval by ID. Producers must register schemas before publishing; consumers use schema IDs embedded in message envelopes to deserialize payloads.

The service handles approximately 50,000 schema lookups per day with a peak of 200 requests per second during high-throughput ingestion windows. It runs as a Lambda-backed API on Node.js 20 with DynamoDB as the backing store for schema versions and compatibility rules.

## Architecture

- **REST API**: Lambda functions handle schema registration (`POST /schemas`), compatibility checks (`POST /compatibility`), and schema lookup by ID or subject-version (`GET /schemas/{id}`, `GET /subjects/{subject}/versions/{version}`).
- **Compatibility Engine**: Enforces configured compatibility modes per subject (BACKWARD, FORWARD, FULL). Rejects registrations that violate the configured mode for a subject.
- **Storage**: DynamoDB table with schema ID as partition key; GSI on subject name for version listing. Schema content stored as a JSON column; parsed at read time.
- **Caching**: Lambda environment-level in-memory cache (512 KB LRU) reduces DynamoDB reads for frequently accessed schemas. Cache is invalidated on Lambda cold start.

## Repositories

- [schema-registry-service](https://git.example.com/acme/schema-registry-service) - Lambda functions, DynamoDB table definitions, compatibility tests

## Runtime Environment

- **Platform**: Lambda / Node.js 20 / DynamoDB
- **Concurrency**: Up to 100 concurrent Lambda executions; provisioned concurrency of 5 to avoid cold-start latency during ingestion bursts
- **Deployment**: SAM-based deployments via ArgoCD

## Dependencies

- Data Quality Monitor - queries schema registry to validate that received schemas match expected versions
- Event Streaming Platform - all Kafka producers and consumers call the registry for schema resolution

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly uptime |
| Schema lookup latency | P99 < 50ms (cached), P99 < 200ms (cache miss) |
| Error rate | < 0.01% 5xx responses |
| Recovery | MTTR < 20 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-042|Schema Registration Failure]]
- [[RUNBOOK-037|Schema Compatibility Violation Response]]
