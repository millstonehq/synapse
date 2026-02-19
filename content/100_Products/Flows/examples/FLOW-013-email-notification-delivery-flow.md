---
id: FLOW-013
type: flow
title: Email Notification Delivery Flow
status: draft
owner: QA Engineer
created: '2024-08-12T19:13:07.095Z'
updated: '2026-02-22T08:43:45.760Z'
tags:
  - flow
  - notification-service
summary: Email Notification Delivery Flow
feature_area: Notification Service
related_prds:
  - PRD-019
example: true
---

## Steps

### Step 1: Notification Request Submission

A producer service submits a notification request to the Notification Routing Engine via `POST /v1/notifications` with `channel: email` or `channel: all`. The request includes the userId, notification type, template reference (slug + version), variable map, and priority level. The routing engine validates the payload schema and returns `202 Accepted` with a `notificationId`.

### Step 2: Routing Decision

The Notification Routing Engine evaluates the routing pipeline for the request: checks the user's global opt-out status, email channel opt-out, quiet hours, and daily frequency cap. If all checks pass, the engine creates a routing decision with `channel: email` and publishes the notification job to the NORMAL-priority RabbitMQ email exchange. If the user has opted out of email, the notification is either suppressed or rerouted to an alternative channel depending on the producer's fallback configuration.

### Step 3: Template Rendering

The Email Delivery Service consumer picks up the job from the queue. It calls the template renderer with the `(templateSlug, version, locale, variableMap)` tuple. The renderer loads the compiled template AST from the LRU cache (or fetches from PostgreSQL on cache miss), validates that all required variables are present in the variable map, and renders the HTML and plain-text bodies. If rendering fails due to a missing variable, the job is sent to the dead-letter queue for investigation.

### Step 4: Provider Submission

The Email Delivery Service suppression layer checks the user's email address against the bounce, complaint, and unsubscribe lists. If the address is suppressed, the job is discarded and the routing decision is logged as `SUPPRESSED`. For non-suppressed addresses, the service submits the rendered email to the primary provider (SendGrid) via the provider adapter. On provider submission failure, the circuit breaker tracks the error and may trigger failover to Mailgun.

### Step 5: Delivery Confirmation

SendGrid (or Mailgun on failover) attempts delivery to the recipient's inbox. Delivery receipts (delivered, bounced, complained) are received asynchronously via webhook. The Email Delivery Service records the receipt in the delivery log, updates the suppression list for hard bounces, and publishes a `notification.delivered` or `notification.failed` event to RabbitMQ for analytics consumers.

## Expected Results

- Email is delivered to the user's inbox within 5 seconds of routing decision under normal load
- Hard-bounce addresses are added to the suppression list and excluded from all future sends
- Template rendering failures are captured in the dead-letter queue with full context for debugging
- Delivery receipt events are available in the notification analytics dashboard within 15 minutes
- If SendGrid is unavailable, the circuit breaker triggers Mailgun failover within 90 seconds

## User Info

| Field | Value |
|-------|-------|
| Role | Notification producer (engineering team) |
| Permissions | Can submit notifications for registered producer ID |
| Test account | test-producer@example.com |
| Test notification type | `order.shipped` (configured in staging) |
| Environment | Staging |
