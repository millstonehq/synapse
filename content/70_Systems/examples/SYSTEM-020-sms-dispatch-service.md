---
id: SYSTEM-020
type: system
title: SMS Dispatch Service
status: approved
owner: Notification Engineering
owner_team: Notification Engineering
runtime: Kubernetes / Go 1.22 / ClickHouse / Kafka
created: '2024-09-27T19:02:42.737Z'
updated: '2025-06-18T11:55:10.667Z'
tags:
  - system
  - notification-service
summary: SMS Dispatch Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/sms-dispatch-service
dependencies:
  - Push Notification Gateway
  - Notification Routing Engine
runbooks:
  - RUNBOOK-022
  - RUNBOOK-026
example: true
---

## Overview

The SMS Dispatch Service handles all outbound SMS and MMS messages across the Notification Platform. It consumes dispatch jobs from Kafka, applies carrier-specific formatting rules, selects an SMS provider (Twilio primary, Vonage secondary), and submits the message for delivery. Delivery receipts from providers are consumed asynchronously and written to ClickHouse for analytics.

The service supports both transactional SMS (OTPs, account alerts) and marketing SMS campaigns, with separate queues and rate limits for each category. All phone numbers are validated against the E.164 standard before dispatch, and carrier opt-out registrations (STOP keywords) are enforced in real time.

## Architecture

The service is structured around Kafka consumer groups with provider adapters:

- **Consumer Layer**: Two Kafka consumer groups — `sms-transactional` (high priority, low throughput) and `sms-marketing` (lower priority, high throughput, rate-limited). Each group processes jobs independently.
- **Number Validation**: E.164 format enforcement and country-level routing rules applied before provider selection.
- **Provider Adapter Layer**: Twilio and Vonage adapters behind a common `SmsProvider` interface. Circuit breaker triggers Vonage failover after 5 errors in 30 seconds.
- **Opt-Out Enforcement**: STOP keyword registrations and carrier-reported opt-outs are stored in a PostgreSQL table and checked before each send.
- **Analytics Layer**: Delivery receipt webhooks from providers are consumed and written to ClickHouse for delivery rate and carrier performance dashboards.

## Repositories

- [sms-dispatch-service](https://git.example.com/acme/sms-dispatch-service) - Application code, migrations, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes cluster across 3 availability zones
- **Language**: Go 1.22
- **Replicas**: 3 pods minimum, autoscaling to 8 based on Kafka consumer lag
- **Resources**: 256Mi memory request / 512Mi limit, 250m CPU request / 500m CPU limit per pod
- **Deployment**: Rolling via ArgoCD
- **Configuration**: Environment variables via ConfigMaps; Twilio and Vonage credentials via Kubernetes Secrets with 90-day rotation

## Dependencies

- Kafka (3-node cluster) - inbound dispatch jobs and outbound delivery receipt events
- ClickHouse - delivery analytics and carrier performance data
- PostgreSQL - opt-out registry and message audit log
- Twilio API - primary SMS provider
- Vonage API - fallback SMS provider
- Notification Routing Engine - inbound job source

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Dispatch latency | P95 < 3s from job receipt to provider submission (transactional) |
| Delivery rate | > 97% of non-opted-out sends accepted by provider |
| Error rate | < 1% unretryable failures under normal conditions |

## Runbooks

- [[RUNBOOK-022|SMS Dispatch Service - High Error Rate]]
- [[RUNBOOK-026|SMS Dispatch Service - Provider Failover]]
