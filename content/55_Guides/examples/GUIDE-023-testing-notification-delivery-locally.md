---
id: GUIDE-023
type: guide
title: Testing Notification Delivery Locally
status: approved
owner: Developer Experience
created: '2024-05-06T12:10:35.674Z'
updated: '2026-06-12T03:41:48.388Z'
tags:
  - guide
  - notification-service
summary: Testing Notification Delivery Locally
audience: partner
related_systems:
  - SYSTEM-020
  - SYSTEM-017
related_sops:
  - SOP-038
  - SOP-040
example: true
---

## Why This Matters

Testing notification delivery in production is dangerous — you'll send real messages to real users. Testing in staging sends to sandboxed providers but requires a deployed environment. This guide shows you how to test the full notification pipeline locally using the Notification Service dev mode, without sending anything to real providers.

## Prerequisites

You need Docker and the Notification Service CLI installed. The local stack runs:
- A local SQS stub (ElasticMQ) for the notification queue
- The Notification Service in `--dev-mode` flag, which routes all dispatches to the local Mailhog/Pushover stub instead of real providers
- A local PostgreSQL instance for preference and delivery tracking

Start the stack with:
```
docker compose -f docker-compose.dev.yml up
```

## Sending a Test Notification

Once the local stack is running, publish a notification event to the local SQS queue using the CLI:

```
npx notification-cli send \
  --notification-id "$(uuidgen)" \
  --recipient-id "test-user-001" \
  --template-id "order-confirmation-v2" \
  --channel email \
  --priority normal \
  --payload '{"order_id": "ORD-12345", "total": "$59.99"}'
```

The Notification Service will process the event and route it to Mailhog (for email) or the push stub. View delivered email at `http://localhost:8025` in Mailhog's web UI.

## Validating Your Payload Schema

Before writing integration code, validate your payload against the schema:

```
npx notification-cli validate --template-id order-confirmation-v2 --payload payload.json
```

This checks required fields, variable binding against the template's `variables.json`, and payload size limits. Fix all validation errors before publishing to any queue — the real Notification Service will reject invalid payloads with a 422 and not queue them for retry.

## Next Steps

Once local testing passes, deploy to the staging environment and run an end-to-end test with a staging recipient (your own email/phone). Staging uses real providers in sandbox mode, so no real users are affected. Check the staging Notification Service dashboard to confirm delivery success before opening a PR.
