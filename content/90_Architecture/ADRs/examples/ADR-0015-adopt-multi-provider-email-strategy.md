---
id: ADR-0015
type: adr
title: Adopt Multi-Provider Email Strategy
status: approved
owner: Tech Lead
created: '2025-08-18T10:15:54.591Z'
updated: '2026-09-17T02:03:24.277Z'
tags:
  - adr
  - notification-service
summary: Adopt Multi-Provider Email Strategy
example: true
---

## Context

The Notification Platform's Email Delivery Service currently uses a single email provider (SendGrid) for all outbound email. A 2-hour SendGrid outage in December 2024 (POSTMORTEM-017) caused 94,000 notifications to be delayed, with no automatic recovery path. The incident exposed a critical single point of failure in the email delivery path.

We need to eliminate the single-provider dependency. Options range from configuring a secondary provider with manual failover, to full active-active multi-provider routing, to building in-house SMTP infrastructure. The solution must be operational within 6 weeks to address the architectural gap before the Q2 campaign season.

The Email Delivery Service currently uses the `EmailProvider` abstraction interface introduced in the original design, which makes multi-provider support technically straightforward to add.

## Decision

We will adopt a **primary/fallback dual-provider strategy** using SendGrid as the primary provider and Mailgun as the automatic failover. The Email Delivery Service circuit breaker will monitor SendGrid error rates and automatically switch to Mailgun when the error rate exceeds 5% over a 60-second window. Recovery back to SendGrid will occur after a 5-minute cool-down period with a gradual traffic shift.

Both providers will be configured and warm at all times (not just on failover). Monthly test sends will be routed through Mailgun to keep credentials active and verify end-to-end delivery capability.

## Consequences

**Positive:**
- Eliminates the single provider outage as a failure mode for email delivery
- Automatic failover completes within 90 seconds, well within user-visible impact thresholds
- Both providers already support our domain authentication (SPF, DKIM, DMARC) so deliverability reputation is preserved during failover
- Monthly warmup sends keep Mailgun credentials and delivery reputation active without requiring manual testing

**Negative:**
- Adds ~$200/month in Mailgun base costs for the standby configuration
- Two provider integrations to maintain and monitor for API changes
- Deliverability reputation must be managed on both providers separately

**Neutral:**
- The circuit breaker thresholds (5% error rate, 60-second window, 5-minute recovery) are initial values and will be tuned based on observed provider behavior

## Alternatives Considered

**Active-active split routing (50/50 across both providers):**
- Pro: No single provider handles all traffic; inherently resilient
- Con: Deliverability reputation is split across two providers, reducing the sending reputation built on each; more complex to monitor and attribute delivery failures
- Rejected because: Reputation dilution outweighs the resilience benefit for our send volumes; primary/fallback achieves the same resilience goal

**In-house SMTP infrastructure (Postfix cluster):**
- Pro: Zero per-message costs at scale; full control over deliverability configuration
- Con: Significant operational burden; ISP reputation management is a full-time specialty; would take 6+ months to implement and warm properly
- Rejected because: Timeline and operational cost are incompatible with the immediate need to address the single-provider risk
