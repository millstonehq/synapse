---
id: RUNBOOK-070
type: runbook
title: Stripe Billing Webhook Failure Runbook
status: deprecated
owner: On-Call Engineer
created: '2024-11-28T15:17:00.313Z'
updated: '2025-08-01T02:27:06.505Z'
tags:
  - runbook
  - billing-engine
summary: Stripe Billing Webhook Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `billing_stripe_webhook_failure_rate_high` - Stripe webhook endpoint returning non-2xx responses at a rate above 2% for 5 minutes
- `billing_stripe_webhook_processing_lag` - Time between Stripe event creation and billing DB update exceeds 10 minutes
- `billing_stripe_webhook_dlq_depth_high` - Stripe webhook dead-letter queue depth exceeds 10 items
- `billing_payment_status_stale` - Payment records not updated within 15 minutes of expected Stripe event

## Diagnosis Steps

1. **Check the Stripe webhook endpoint health** - Query the billing service logs for `stripe-webhook` requests in the last 30 minutes. Check response status codes. 4xx errors typically indicate signature verification failures or malformed payloads; 5xx indicate internal processing errors.
2. **Check Stripe signature verification** - If webhook requests are returning 401 or 400 with "Invalid signature", the `BILLING_STRIPE_WEBHOOK_SECRET` environment variable may have been rotated in Stripe but not updated in the billing service. Check #billing-deployments for any recent secret rotation.
3. **Check the webhook dead-letter queue** - Navigate to the billing admin console and check the Stripe webhook DLQ. Review the failed events to identify the error type (signature failure, payment not found, duplicate event, schema error).
4. **Check the Stripe dashboard** - Log in to the Stripe dashboard and review webhook delivery attempts. Stripe shows delivery status, response codes, and allows manual event replay. This is the source of truth for what Stripe sent.
5. **Check billing payment record status** - If specific payment records are stale, query the billing DB: `SELECT id, status, updated_at FROM payments WHERE stripe_payment_intent_id = ? ORDER BY updated_at DESC;`. Stale `PENDING` status indicates the webhook was not processed.

## Remediation Steps

1. **If webhook signature verification is failing**: Update the `BILLING_STRIPE_WEBHOOK_SECRET` in the billing service Kubernetes secret to match the current Stripe webhook signing secret. Restart the billing service to pick up the new secret.
2. **If Stripe events are in the DLQ**: Reprocess DLQ events via the billing admin console **Stripe Webhooks > Reprocess DLQ**. For critical events (payment confirmations), replay from the Stripe dashboard directly using the event ID.
3. **If specific payment intents are stuck in PENDING**: Manually trigger a payment status sync for the affected payment intent IDs via the billing admin console **Payments > Sync from Stripe**.
4. **If the billing service is returning 5xx to Stripe**: Stripe will retry webhook delivery for up to 72 hours. Focus on fixing the internal processing error first (check logs for the exception), then verify Stripe retries or manually replay missed events from the Stripe dashboard.
5. **If Stripe itself has an incident**: Check the Stripe status page (status.stripe.com). If Stripe is experiencing webhook delivery issues, events will be delivered with delay when Stripe recovers. No action needed beyond monitoring.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks webhook error rate and Stripe dashboard |
| 15 min | Post assessment in #billing-incidents: failure type, affected payment count |
| 30 min | If payment confirmations are missed affecting active invoices: page Billing Platform tech lead |
| 45 min | If the issue is not resolving: contact Stripe support with merchant ID and webhook endpoint ID |
| 60 min | If payment status cannot be reconciled: page Engineering Manager and notify Finance Operations |

## Dashboards

- [Stripe Webhook Health](https://grafana.example.com/d/billing-stripe-webhooks) - Webhook receive rate, success/failure rate, DLQ depth
- [Billing Payment Status](https://grafana.example.com/d/billing-payments) - Payment status distribution, stale payment count
- [Billing Engine Logs](https://kibana.example.com/app/discover#/billing) - Stripe webhook handler errors with event IDs
- [Stripe Dashboard](https://dashboard.stripe.com/webhooks) - Webhook delivery history, event replay
