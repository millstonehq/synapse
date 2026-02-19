---
id: SYSTEM-041
type: system
title: Customer Portal Web Application
status: deprecated
owner: Customer Engineering
owner_team: Customer Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2024-10-13T05:22:40.360Z'
updated: '2026-10-30T02:25:04.511Z'
tags:
  - system
  - customer-portal
summary: Customer Portal Web Application
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/customer-portal-web-application
dependencies:
  - Customer Preference Service
  - Customer Support Widget Service
runbooks:
  - RUNBOOK-058
  - RUNBOOK-057
example: true
---

## Overview

The Customer Portal Web Application is the primary web interface through which customers interact with their accounts. It handles authenticated session management, account dashboards, support ticket submission, and preference configuration. The application serves as the front-end layer coordinating with the Customer API Gateway and downstream microservices.

The application is deployed on Kubernetes with Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13 and targets 99.95% monthly uptime. It depends on the Customer Preference Service for personalization data and the Customer Support Widget Service for embedded support functionality.

## Architecture

The portal follows a server-side-rendered architecture with client-side hydration for interactive widgets:

- **Presentation Layer**: Next.js pages and React components consuming the Customer API Gateway via GraphQL. Server components handle SEO-critical rendering; client components handle real-time updates.
- **Session Layer**: JWT-based authentication with short-lived access tokens and rotating refresh tokens stored in httpOnly cookies.
- **Integration Layer**: All data access goes through the Customer API Gateway. The web application does not connect directly to any backend database.
- **Widget Layer**: The Customer Support Widget Service is embedded as an iframe component loaded asynchronously so support widget failures do not impact core portal functionality.
- **Asset Layer**: Static assets (JS bundles, CSS, images) served via CDN with cache-busting content hashes.

## Repositories

- [customer-portal-web-application](https://git.example.com/acme/customer-portal-web-application) - Application code, Next.js config, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
- **Replicas**: 3 pods minimum, autoscaling to 8 on CPU (65%) and request rate
- **Deployment**: Rolling deploy via ArgoCD with readiness probe gates
- **TLS**: Terminated at ingress controller; HSTS enforced with max-age 1 year

## Dependencies

- Customer Preference Service - user personalization data, notification settings
- Customer Support Widget Service - embedded support chat and ticket widget
- Customer API Gateway - all API calls are proxied through the gateway

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| P95 page load | < 2s on 4G connection |
| Error rate | < 0.5% 5xx responses |
| Recovery | MTTR < 20 minutes for SEV-1 |

## Runbooks

- [[RUNBOOK-079|Customer Portal SSL Certificate Runbook]]
