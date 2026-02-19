---
id: SYSTEM-003
type: system
title: Payment Reconciliation Engine
status: deprecated
owner: Payment Engineering
owner_team: Payment Engineering
runtime: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7
created: '2024-08-21T05:20:01.691Z'
updated: '2025-11-25T15:49:03.906Z'
tags:
  - system
  - payment-processing
summary: Payment Reconciliation Engine
sla: 99.9% monthly uptime
repos:
  - https://git.example.com/acme/payment-reconciliation-engine
dependencies:
  - Transaction Ledger Service
  - Payment Gateway Service
runbooks:
  - RUNBOOK-001
  - RUNBOOK-003
example: true
---

## Overview

The Payment Reconciliation Engine is a batch processing service that reconciles internal transaction records against gateway settlement reports from Stripe and PayPal. It identifies discrepancies between what the platform recorded and what the payment provider actually settled, flagging mismatches for investigation and generating daily reconciliation reports for the finance team.

Note: this service is deprecated and being replaced by an enhanced reconciliation pipeline. Existing functionality remains in production until migration is complete.

## Architecture

The engine runs as a scheduled batch job rather than a continuously serving API:

- **Ingestion**: Pulls settlement CSV/JSON exports from Stripe and PayPal via their reporting APIs on a nightly schedule (02:00 UTC).
- **Matching**: Joins gateway settlement records against the Transaction Ledger Service records by gateway reference ID, amount, and currency.
- **Discrepancy Detection**: Flags records where settlement amount differs from captured amount by more than $0.01, or where gateway shows settled but internal state is not `settled`.
- **Reporting**: Writes a daily reconciliation summary to PostgreSQL and publishes a report event to SQS for the finance notification pipeline.

## Repositories

- [payment-reconciliation-engine](https://git.example.com/acme/payment-reconciliation-engine) - Application code, SQL reports, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes CronJob running nightly at 02:00 UTC
- **Language**: Go 1.22
- **Resources**: 1Gi memory request / 2Gi limit (large in-memory join for daily batch)
- **Deployment**: Image updated via ArgoCD on merge to main

## Dependencies

- PostgreSQL 15 - reads from transaction_ledger, writes reconciliation results
- Redis 7 - job deduplication lock (prevents double-run if CronJob overlaps)
- Transaction Ledger Service - source of internal settled records
- Payment Gateway Service - gateway API credentials for pulling settlement reports

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% monthly (batch job completion rate) |
| Reconciliation lag | Reports available by 06:00 UTC each morning |
| Discrepancy detection | < 0.01% undetected discrepancy rate |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- See RUNBOOK-001 and RUNBOOK-003 for reconciliation failure response procedures.
