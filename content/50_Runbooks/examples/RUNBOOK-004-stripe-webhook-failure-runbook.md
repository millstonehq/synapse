---
id: RUNBOOK-004
type: runbook
title: Stripe Webhook Failure Runbook
status: draft
owner: On-Call Engineer
created: '2024-03-22T00:46:35.533Z'
updated: '2026-07-18T03:59:29.319Z'
tags:
  - runbook
  - payment-processing
summary: Stripe Webhook Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `StripeWebhookFailureRateHigh` — Stripe webhook endpoint returning non-2xx responses for more than 5% of deliveries in a 10-minute window
- `StripeWebhookProcessingLag` — webhook processing queue depth exceeds 500 events
- `StripeWebhookSignatureVerificationFailing` — HMAC signature verification failures rate exceeds 1% (possible key rotation issue)
- `StripeWebhookEndpointUnreachable` — Stripe reports the webhook endpoint as unreachable in their dashboard

## Diagnosis Steps

1. **Check Stripe webhook dashboard** - Log in to the Stripe dashboard and navigate to Developers > Webhooks; check the endpoint health and recent delivery attempts to identify the failure pattern.
2. **Inspect webhook consumer logs** - Query payment service logs for `stripe_webhook` events returning 4xx/5xx; identify whether failures are on specific event types or all events.
3. **Verify webhook signature configuration** - Confirm the `STRIPE_WEBHOOK_SECRET` in the secrets manager matches the endpoint signing secret shown in the Stripe dashboard; a mismatch causes all signature verifications to fail.
4. **Check endpoint availability** - Verify the webhook endpoint is reachable by checking the load balancer access logs; 502/504 responses indicate the payment service is unhealthy behind the load balancer.
5. **Review recent code changes** - Check for recent changes to the webhook handler code; schema changes or new required fields in event processing are a common cause of sudden failures.

## Remediation Steps

1. **If signature secret mismatch**: Update the `STRIPE_WEBHOOK_SECRET` in the secrets manager to match the Stripe dashboard value; trigger a rolling restart to pick up the new secret; replay failed deliveries from Stripe dashboard.
2. **If endpoint unreachable**: Investigate payment service health; restore the service per the health check runbook; Stripe will automatically retry undelivered events within 72 hours.
3. **If specific event type failing**: Deploy a fix for the failing handler or add a bypass for the problematic event type to unblock the queue; file a bug ticket for the fix.
4. **If processing lag is growing**: Scale up the webhook consumer service; confirm queue depth is decreasing before reducing scale.
5. **If Stripe reports 429 rate limiting**: Reduce webhook consumer concurrency; contact Stripe support if rate limits appear misconfigured on their side.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks Stripe dashboard and signature configuration |
| 15 min | If signature issue or endpoint unreachable, notify Engineering Manager |
| 30 min | Engineering Manager escalates if financial events (payment.succeeded, charge.refunded) are affected |
| 60 min | Director of Engineering engaged; assess whether payment state inconsistencies require manual reconciliation |

## Dashboards

- [Stripe Webhook Processing](https://grafana.example.com/d/stripe-webhooks) - Delivery rate, processing lag, and failure breakdown by event type
- [Payment Event Queue](https://grafana.example.com/d/payment-events) - Queue depth and consumer throughput
- [Payment Service Endpoint Health](https://grafana.example.com/d/payment-endpoint) - Load balancer access logs and response code distribution
