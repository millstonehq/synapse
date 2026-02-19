---
id: GUIDE-055
type: guide
title: Getting Started with Billing API
status: accepted
owner: Developer Experience
created: '2024-01-05T02:45:15.288Z'
updated: '2025-02-02T17:10:45.923Z'
tags:
  - guide
  - billing-engine
summary: Getting Started with Billing API
audience: internal
related_systems:
  - SYSTEM-050
  - SYSTEM-046
related_sops:
  - SOP-100
  - SOP-096
example: true
---

## Why This Matters

The Billing API is the authoritative interface for all billing operations on the platform. Any service that needs to retrieve customer billing status, create invoices, apply credits, or query usage records must go through this API. Using it correctly from the start prevents billing errors that are difficult to reverse and may affect customer charges.

This guide covers authentication, key concepts, and the most common integration patterns. By the end, you should be able to make authenticated requests, retrieve invoice data, and understand how the Billing API fits into the broader billing lifecycle.

## Prerequisites

Before making your first Billing API call, ensure you have:

- A service account with the appropriate billing API role (request via the access management system)
- The Billing API base URL for your environment (staging: `https://billing-api.staging.example.com`, production: `https://billing-api.example.com`)
- An API key or OAuth client credentials issued for your service account

## Authentication and Key Concepts

The Billing API uses OAuth 2.0 client credentials for service-to-service authentication. Request a token from the identity service using your client ID and secret, then include it as a Bearer token in the `Authorization` header of every request.

All monetary amounts are returned as integers in the smallest currency unit (cents for USD). A value of `10050` means $100.50. This is intentional — it prevents floating-point precision issues. Always use the `currency` field alongside any amount field to determine the currency and its minor unit denominator.

Idempotency keys are required for all write operations. Include a `Idempotency-Key` header with a unique UUID per operation attempt. The Billing API will return the same response for duplicate requests with the same key within a 24-hour window, making retries safe.

## Making Your First Request

Retrieve the current billing status for an account:

```
GET /v1/accounts/{account_id}/billing-summary
Authorization: Bearer {token}
```

The response includes the current plan, next invoice date, current balance, and pending credits. This is the most common endpoint used by product surfaces that need to display billing information.

To list recent invoices for an account:

```
GET /v1/accounts/{account_id}/invoices?limit=10
Authorization: Bearer {token}
```

Use the `cursor` field from the response `meta.next_cursor` to paginate through older invoices.

## Common Questions

**How do I test in staging without affecting real billing?** Staging uses test account fixtures prefixed with `TEST-`. All billing operations on `TEST-` accounts are non-destructive and do not trigger payment collection or real email delivery.

**What if I get a 429 Too Many Requests?** The Billing API enforces rate limits per service account. Retry with exponential backoff using the `Retry-After` header value. Sustained high volume requires a rate limit increase request.

## Next Steps

- Review the Billing API Response Standard for the complete error format reference
- Explore the usage events endpoint if your service needs to submit metering data
- Check the Testing Billing Scenarios Guide for test data patterns
