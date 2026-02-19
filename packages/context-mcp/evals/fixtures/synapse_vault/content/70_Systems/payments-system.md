---
id: payments-system
type: system
title: Payments API System
status: approved
owner: Platform Team
owner_team: Payments Engineering
runtime: Node.js 20 / Express
created: "2025-05-15T00:00:00.000Z"
updated: "2026-02-19T00:00:00.000Z"
tags:
  - system
  - payments
  - api
  - stripe
  - paypal
summary: Production payment processing API system documentation supporting multiple providers.
repos:
  - payments-api
sla: "99.9%"
dependencies:
  - stripe-api
  - paypal-api
  - mongodb
runbooks:
  - payments-incident-runbook
---

## Summary

The Payments API system handles all payment processing for the platform. It integrates with multiple payment providers (Stripe and PayPal) for credit card processing and uses MongoDB for transaction records.

## Architecture

Single Express.js service deployed on Kubernetes. Communicates with:
- **Stripe API**: For Stripe payment processing (charges and refunds)
- **PayPal API**: For PayPal payment processing (charges and refunds)
- **MongoDB**: For local transaction records and user payment history

### System Diagram

```
Client → API Gateway → Payments API → Stripe API
                                    → PayPal API
                                    → MongoDB
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `PAYPAL_CLIENT_ID` | PayPal API client ID |
| `PAYPAL_SECRET` | PayPal API secret key |
| `DATABASE_URL` | MongoDB connection string |
| `PORT` | Service port (default: 3000) |

### Rate Limiting

- 100 requests per 15 minutes per IP address
- Enforced at the application level via express-rate-limit

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments/charge` | Create a charge via selected provider |
| POST | `/payments/refund` | Refund a charge (provider auto-detected) |
| GET | `/payments/history` | Get user payment history (all providers) |

## Monitoring

- Health check: `GET /health`
- Stripe webhook: `POST /webhooks/stripe`
- PayPal webhook: `POST /webhooks/paypal`
- Metrics exported to Prometheus

## Incident Response

See [[payments-incident-runbook]] for incident procedures. Key alerts:
- Payment provider API error rate > 5%
- Payment success rate < 90%
- Response time P99 > 5s
