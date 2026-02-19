---
id: POLICY-018
type: policy
title: Notification Rate Limiting Policy
status: approved
owner: CISO
created: '2024-03-12T08:52:24.113Z'
updated: '2026-10-09T01:07:53.701Z'
tags:
  - policy
  - notification-service
summary: Notification Rate Limiting Policy
example: true
related_standards:
  - STANDARD-022
  - STANDARD-020
---

## Scope

This policy governs rate limits applied to all outbound notification channels operated by the Notification Service, including email, SMS, push, and in-app messages. It applies to all internal services that publish notification events and to any third-party integrations that send notifications on behalf of the platform.

## Rationale

- Uncontrolled notification volume degrades third-party provider relationships and increases per-message costs
- Notification flooding caused by bugs or misconfigured triggers can result in mass user opt-outs and reputational damage
- SMS and email providers enforce their own rate limits; exceeding them causes queuing delays that violate SLAs
- Rate limiting is a defense-in-depth control against runaway loops in event-driven notification pipelines

## Policy Statements

- Each notification channel must enforce per-user rate limits to prevent individual users from receiving excessive messages in a short timeframe
- Default per-user limits are: email 10/day, SMS 3/day, push 20/day; critical system alerts are exempt
- Burst sending above 1,000 messages per minute on any single channel requires pre-approval from the Notification Service team lead
- Automated campaigns must implement a send-rate cap and distribute volume across a defined send window
- Rate limit breaches must be logged and reviewed within 24 hours; repeated breaches trigger a mandatory configuration review
- All notification pipelines must include a circuit breaker that halts dispatch if error rates exceed 10% for 2 consecutive minutes

## Related Standards

- [[STANDARD-022|SMS Gateway Integration Standard]]
- [[STANDARD-020|Email Template Coding Standard]]
