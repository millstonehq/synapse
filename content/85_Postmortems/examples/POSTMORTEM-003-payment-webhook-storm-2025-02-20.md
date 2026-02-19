---
id: POSTMORTEM-003
type: postmortem
title: Payment Webhook Storm 2025-02-20
status: review
owner: On-Call Engineer
created: '2025-05-18T05:27:20.669Z'
updated: '2025-03-04T07:27:02.528Z'
tags:
  - postmortem
  - payment-processing
summary: Payment Webhook Storm 2025-02-20
incident_number: INC-74
severity: SEV-2
incident_date: '2026-01-07'
detection_time: '2025-11-01T06:50:24.838Z'
resolution_time: '2025-02-07T22:42:16.153Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-003
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 20, 2025, Stripe executed a historical backfill of webhook events for a window of missed deliveries from a prior Stripe-side infrastructure issue. This caused approximately 14,000 webhook events to be delivered to the Payment Webhook Dispatcher over 20 minutes — roughly 70x the normal event rate. The dispatcher's SQS queue depth spiked significantly and consumer processing lagged by up to 2 hours before catching up. No payment state errors resulted, but downstream systems relying on near-real-time webhook delivery experienced delays.

## Timeline

- **09:42** - Stripe sends notification email that a historical webhook backfill is starting (not monitored in real-time)
- **09:45** - Webhook event ingest rate spikes from ~200/min to ~14,000/min
- **09:47** - SQS queue depth alert fires: `payments_webhook_queue_depth_high` (threshold: 500 messages)
- **09:50** - On-call acknowledges alert and begins investigation
- **09:55** - On-call identifies the backfill as the source by reviewing Stripe dashboard
- **10:05** - Webhooks are being processed correctly — no errors — but consumer lag is growing
- **10:30** - Last Stripe backfill event received. Queue depth at peak: 12,400 messages
- **11:15** - Notification service alerts customers of payment confirmations that had been delayed 45–90 minutes
- **11:45** - Queue depth below 1,000 messages. Consumer is catching up.
- **12:10** - Queue fully drained. All events processed. Incident monitored and closed.

## Impact

- **Duration**: ~2 hours of webhook processing lag (09:45 - 12:10 UTC)
- **Payment state errors**: Zero — no transactions were double-processed or lost
- **Customer impact**: Payment confirmation emails delayed by 45–90 minutes for approximately 1,800 customers
- **SLA impact**: No availability SLA breach. Webhook delivery SLA (P95 < 5 min) was breached for the duration.

## Root Cause Analysis

1. **No inbound rate limiting on webhook receiver**: The webhook dispatcher accepted all events without any rate limiting or backpressure mechanism. Stripe's backfill was able to overwhelm the consumer workers, which are sized for normal throughput.

2. **No alerting on Stripe email notifications**: Stripe sent a pre-backfill notification email, but this was not monitored or routed to the on-call channel. Earlier awareness would have allowed pre-scaling consumer workers.

## Resolution

1. Monitored queue depth and confirmed events were processing correctly with no errors
2. Scaled webhook consumer workers from 2 to 6 to accelerate catch-up processing
3. Queue fully drained approximately 2 hours after storm began

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement per-source rate limiting in webhook receiver (max 1,000 events/min) | Payments team | P1 | 2025-03-07 | Completed |
| Route Stripe notification emails to #payments-alerts Slack channel | Platform | P2 | 2025-03-01 | Completed |
| Add auto-scaling rule: scale consumer workers when queue depth > 1,000 | SRE | P2 | 2025-03-14 | In progress |
| Add webhook delivery lag metric to SLA dashboard | SRE | P3 | 2025-03-21 | Pending |

## Lessons Learned

- **What went well**: The dispatcher processed all events without errors. No payment state corruption occurred. Consumer scaling resolved the backlog within a reasonable time window.
- **What went poorly**: On-call was not aware of the Stripe backfill notification before the alert fired. The lack of inbound rate limiting meant we had no control over the event ingest rate.
- **What was lucky**: Stripe sent the notification email before starting the backfill. Had they not, there would have been no early warning at all.
