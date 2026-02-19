---
id: SYSTEM-044
type: system
title: Customer Support Widget Service
status: approved
owner: Customer Engineering
owner_team: Customer Engineering
runtime: Kubernetes / Go 1.22 / ClickHouse / Kafka
created: '2025-07-14T04:45:44.170Z'
updated: '2026-10-13T11:11:14.893Z'
tags:
  - system
  - customer-portal
summary: Customer Support Widget Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/customer-support-widget-service
dependencies:
  - Customer Analytics Service
  - Customer Portal Web Application
runbooks:
  - RUNBOOK-062
  - RUNBOOK-061
example: true
---

## Overview

The Customer Support Widget Service provides an embeddable support interface rendered within the Customer Portal Web Application. It manages live chat session initiation, support ticket creation and status, FAQ search, and escalation routing to human agents. The widget is loaded asynchronously to ensure portal performance is not degraded if the widget service is unavailable.

The service is built on Kubernetes / Go 1.22 / ClickHouse / Kafka and targets 99.99% monthly uptime, reflecting that customers expect support access to be highly available.

## Architecture

- **Widget Embed API**: Returns JavaScript snippet and initial state for the support widget. Cached aggressively at CDN level (TTL 5 min).
- **Chat Session Service**: WebSocket-based session handling. Sessions are stateful; connection state is stored in Redis with 30-minute idle TTL.
- **Ticket Service**: Creates, reads, and updates support tickets. Ticket data stored in ClickHouse for high-volume analytics queries.
- **FAQ Search**: Full-text search over the knowledge base, backed by ClickHouse's built-in full-text indexes.
- **Event Streaming**: Kafka topics consume portal activity events (page views, error encounters) to enable proactive support suggestions.

## Repositories

- [customer-support-widget-service](https://git.example.com/acme/customer-support-widget-service) - Service code, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Go 1.22 / ClickHouse / Kafka
- **Replicas**: 4 pods minimum, autoscaling to 12 based on WebSocket connections
- **Deployment**: Blue-green via ArgoCD; WebSocket draining handled during rollout
- **TLS**: TLS 1.3 for all WebSocket connections

## Dependencies

- Customer Analytics Service - receives widget interaction events for funnel analysis
- Customer Portal Web Application - primary host for the embedded widget
- Redis - WebSocket session state
- Kafka - portal activity event stream

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Chat session init | < 500ms P95 |
| Ticket creation | < 1s P95 |
| Recovery | MTTR < 15 minutes for SEV-1 |

## Runbooks

- [[RUNBOOK-079|Customer Portal SSL Certificate Runbook]]
