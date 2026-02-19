---
id: SYSTEM-049
type: system
title: Tax Calculation Engine
status: approved
owner: Billing Engineering
owner_team: Billing Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2025-09-05T07:26:40.461Z'
updated: '2026-11-06T20:56:18.363Z'
tags:
  - system
  - billing-engine
summary: Tax Calculation Engine
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/tax-calculation-engine
dependencies:
  - Billing Event Processor
  - Usage Metering Service
runbooks:
  - RUNBOOK-066
  - RUNBOOK-065
example: true
---

## Overview

The Tax Calculation Engine is responsible for computing applicable taxes on all billable amounts within the Billing Engine. It integrates with Avalara's AvaTax API as the primary tax determination provider and applies results to invoice line items during invoice generation. The engine also maintains a local tax result cache to minimize API call volume and meet latency SLAs.

The service handles approximately 120,000 tax calculation requests per day, covering sales tax, VAT, and GST across supported jurisdictions. It depends on the Billing Event Processor for triggering calculations and the Usage Metering Service for usage-based taxable amounts.

## Architecture

- **Tax Calculation API**: Internal REST API accepting line-item requests and returning tax amounts per jurisdiction. Python 3.12 with FastAPI.
- **Avalara Adapter**: Wraps the Avalara AvaTax REST API v2. Handles retry logic (3 attempts, exponential backoff) and circuit breaker (5 failures in 30s triggers open state).
- **Result Cache**: Redis 7 caches tax calculation results keyed by (customer_id, address_hash, line_items_hash) with a 1-hour TTL. Cache hit rate target: > 60%.
- **Address Validation**: Pre-validates and normalizes customer addresses using Avalara's address validation endpoint before tax calculation.
- **Audit Log**: All tax calculation requests and responses are persisted to OpenSearch for 7-year retention as required by tax compliance obligations.

## Repositories

- [tax-calculation-engine](https://git.example.com/acme/tax-calculation-engine) - Application code, Dockerfile

## Runtime Environment

- **Platform**: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
- **Tasks**: 3 minimum, autoscaling to 10 based on CPU (60%) and request rate
- **Resources**: 1 vCPU / 2 GB memory per task
- **Deployment**: Blue-green via CodeDeploy
- **Secrets**: Avalara API credentials via AWS Secrets Manager with 90-day rotation

## Dependencies

- Avalara AvaTax API - primary tax determination provider
- Redis 7 - tax result caching, 3-node cluster
- OpenSearch cluster - audit log storage and search
- Billing Event Processor - upstream trigger for tax calculations
- Usage Metering Service - provides taxable usage quantities

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Latency | P95 < 800ms (includes Avalara round-trip) |
| Cache hit rate | > 60% of requests served from cache |
| Error rate | < 0.2% 5xx responses |

## Runbooks

- [[RUNBOOK-066|Tax Calculation Engine High Error Rate]]
- [[RUNBOOK-065|Tax Calculation Avalara Circuit Breaker Open]]
