---
id: PROCESS-020
type: process
title: Email Provider Failover Process
status: draft
owner: Platform Lead
created: '2024-10-01T04:05:23.967Z'
updated: '2026-10-02T17:13:07.389Z'
tags:
  - process
  - notification-service
summary: Email Provider Failover Process
related_standards:
  - STANDARD-019
  - STANDARD-023
related_sops:
  - SOP-036
  - SOP-040
related_systems:
  - SYSTEM-018
example: true
---

## Purpose

This process defines how the Notification Service transitions email sending volume from a degraded primary provider to a secondary provider. Email provider outages cause missed transactional messages; a rehearsed failover process minimizes the delivery gap and prevents data loss.

## Scope

- All outbound email delivered via the primary email provider (SendGrid)
- Failover routing to the secondary provider (Amazon SES)
- Reversion to primary provider after incident resolution

## Roles and Responsibilities

- **On-Call Engineer**: Detects the degradation, initiates the failover decision, and executes the routing change
- **Platform Lead**: Provides approval for failover if time permits; is notified immediately regardless
- **Notification Service Team Lead**: Monitors volume and delivery rates during failover and signs off on reversion
- **Incident Commander**: Coordinates if the provider outage constitutes a major incident affecting SLAs

## Triggers

- Primary provider P95 delivery latency exceeds 60 seconds for more than 5 consecutive minutes
- Primary provider error rate exceeds 5% for any 10-minute window
- Primary provider status page indicates an active incident

## Inputs

- Alert from Notification Service monitoring dashboard
- Primary provider status page confirmation
- Current email queue depth and hourly send volume

## Outputs

- Email traffic routed to secondary provider with confirmed delivery resumption
- Incident ticket documenting failover timeline and provider status
- Post-failover delivery rate comparison confirming secondary provider is performing within SLA

## Steps

1. On-Call Engineer confirms the degradation is provider-side (not configuration error) by checking the provider status page and reviewing error logs
2. On-Call Engineer notifies Platform Lead and posts in #notifications-incidents: "Initiating email failover from SendGrid to SES. Reason: [brief description]"
3. On-Call Engineer updates the Notification Service routing configuration to set secondary provider as active
4. On-Call Engineer verifies delivery rate recovers within 5 minutes on the monitoring dashboard
5. On-Call Engineer monitors secondary provider delivery rate for 30 minutes and checks for any SES-specific errors
6. Platform Lead and Team Lead review delivery metrics and confirm failover is stable
7. When primary provider resolves, Team Lead schedules reversion during a low-volume window and follows the same verification steps

## Controls

- Failover configuration changes require a second engineer to confirm the change before it is applied
- Secondary provider must be tested monthly with a low-volume smoke-send to verify credentials and routing
- All failover events must be logged in the incident tracker regardless of duration
- Reversion to primary requires explicit Team Lead sign-off
