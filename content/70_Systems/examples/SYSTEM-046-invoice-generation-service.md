---
id: SYSTEM-046
type: system
title: Invoice Generation Service
status: draft
owner: Billing Engineering
owner_team: Billing Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2024-09-03T09:10:15.150Z'
updated: '2026-06-13T14:40:15.291Z'
tags:
  - system
  - billing-engine
summary: Invoice Generation Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/invoice-generation-service
dependencies:
  - Usage Metering Service
  - Subscription Management Service
runbooks:
  - RUNBOOK-069
  - RUNBOOK-065
example: true
---

## Overview

The Invoice Generation Service is the core component of the Billing Engine responsible for assembling, rendering, and distributing customer invoices at the end of each billing cycle. It consumes finalized usage records from the [[Usage Metering Service]] and subscription entitlements from the [[Subscription Management Service]] to produce itemized invoices in PDF and JSON formats, which are then handed off to the payment collection pipeline and archived for compliance purposes.

The service runs scheduled generation jobs aligned to each customer's billing cadence (monthly, quarterly, or annual) and also supports ad-hoc invoice generation for mid-cycle events such as plan upgrades, credits, and manual adjustments. It processes approximately 120,000 invoices per month with peak load concentrated in the first three business days of each calendar month.

## Architecture

The service is structured around a job-based processing model. A scheduler process reads pending billing periods from PostgreSQL and enqueues generation tasks onto a RabbitMQ work queue. A pool of worker processes consumes these tasks, fetches usage and subscription data from upstream services, applies pricing rules and tax calculations, and renders the final invoice document. Completed invoices are persisted to PostgreSQL and emitted as events for downstream consumers including the payment gateway integration and the customer notification service.

All invoice state transitions (pending → generating → rendered → delivered → paid) are tracked in PostgreSQL with optimistic locking to prevent duplicate generation. The rendering pipeline uses a templating engine to produce PDF output, with locale-aware formatting for currency, dates, and tax line items. A dead-letter queue captures any tasks that fail after three retry attempts, triggering alerts for manual intervention.

## Repositories

- [invoice-generation-service](https://git.example.com/acme/invoice-generation-service) - Application code, worker logic, PDF templates, and database migrations
- [billing-infrastructure](https://git.example.com/acme/billing-infrastructure) - Terraform modules and Kubernetes manifests shared across Billing Engine services
- [billing-shared-libs](https://git.example.com/acme/billing-shared-libs) - Shared Python libraries for pricing rules, tax calculations, and billing event schemas

## Runtime Environment

The service runs on Kubernetes with separate deployments for the scheduler process (single replica) and the worker pool (4 replicas minimum, autoscaling to 16 based on RabbitMQ queue depth). Both components are written in Python 3.12 and packaged as Docker images built via CI. PostgreSQL 16 serves as the system of record for invoice state and document metadata. RabbitMQ 3.13 provides the work queue and dead-letter queue. Generated PDF artifacts are stored in object storage (S3-compatible) with references held in PostgreSQL. Configuration is managed via Kubernetes ConfigMaps and Secrets, with database credentials rotated on a 90-day cycle through the secrets management platform.

## Dependencies

- **Usage Metering Service** - Provides finalized, aggregated usage records per customer per billing period; queried synchronously during invoice generation
- **Subscription Management Service** - Supplies active plan entitlements, pricing tiers, discounts, and billing cadence configuration per account
- **Tax Calculation Service** - Called per invoice to determine jurisdiction-appropriate tax rates and line items based on customer billing address
- **Notification Service** - Receives invoice delivery events asynchronously via RabbitMQ to trigger customer email dispatch
- **Payment Gateway Integration** - Consumes rendered invoice events to initiate charge collection for non-manual payment methods

## SLA

The Invoice Generation Service targets 99.99% monthly uptime for its API and scheduling surfaces. Invoice generation jobs must complete within 15 minutes of their scheduled trigger time for 99% of accounts. P95 latency for on-demand invoice generation requests must remain below 30 seconds. In the event of an upstream dependency outage (e.g., Usage Metering Service unavailable), jobs are held in a pending state and retried automatically once the dependency recovers, with no data loss guaranteed by the durable RabbitMQ queue.

## Runbooks

- [[RUNBOOK-069|Invoice Generation Job Failures and Dead-Letter Queue Remediation]]
- [[RUNBOOK-065|Billing Engine Scheduler Outage Response]]
