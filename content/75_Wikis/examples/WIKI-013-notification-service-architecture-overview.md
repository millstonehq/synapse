---
id: WIKI-013
type: wiki
title: Notification Service - Architecture Overview
status: draft
owner: Notification Team
created: '2024-03-22T13:54:26.193Z'
updated: '2025-09-09T07:53:37.947Z'
tags:
  - wiki
  - notification-service
summary: Notification Service - Architecture Overview
source_repo: https://git.example.com/acme/notification-service
commit_sha: e076be5264ad93f663c9ff4a140c80e87b174f97
generated_at: '2025-02-01T17:53:14.881Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: medium
example: true
---

## Overview

The Notification Service is a centralized, event-driven microservice responsible for delivering transactional and operational messages across multiple channels including email, SMS, push notifications, and in-app alerts. It acts as the single outbound communication layer for the platform, decoupling upstream services from the details of delivery provider integration and channel routing logic.

The service is built in Go and deployed as a Kubernetes workload. It consumes events from an internal SQS queue, resolves recipient preferences, renders templates, and dispatches messages through the appropriate provider. Delivery receipts and failure events are written back to an audit log for observability and retry purposes.

## Architecture

The Notification Service follows a pipeline architecture organized around three phases: ingestion, resolution, and dispatch. Each phase is handled by a distinct layer of the application, allowing individual components to be scaled or replaced independently.

Ingestion is handled by a pool of SQS consumer goroutines that long-poll for incoming notification requests. Resolution involves loading user preferences, selecting the appropriate channel and template, and rendering the final message payload. Dispatch hands the rendered payload to a provider-specific adapter and records the outcome.

Key architectural properties:

- **Stateless workers** — all state is held in PostgreSQL and Redis; workers can be scaled horizontally without coordination
- **Provider abstraction** — all delivery providers implement a common `Notifier` interface, enabling zero-downtime provider swaps
- **Preference-aware routing** — channel selection respects per-user opt-out and frequency-capping rules before dispatch
- **At-least-once delivery** — messages are acknowledged from SQS only after a successful delivery receipt or final retry exhaustion

## Key Components

### `internal/consumer`

SQS consumer pool that receives `NotificationRequest` events. Each worker deserializes the payload, validates the schema, and hands off to the resolution pipeline. The consumer pool size is configurable and defaults to 20 concurrent workers.

### `internal/resolver`

Handles recipient and channel resolution:

- Loads user contact details and channel preferences from the `users` and `preferences` tables
- Applies frequency-cap rules stored in Redis (sliding window counters per user per channel per day)
- Falls back to a secondary channel when the primary is suppressed or unavailable

### `internal/template`

Template rendering engine backed by Go's `text/template` package with a custom function library. Templates are stored in the `notification_templates` table and cached in memory with a 5-minute TTL. The renderer accepts a typed data context and returns a fully-interpolated subject and body.

### `internal/provider`

Provider adapters behind the `Notifier` interface:

- `email/sendgrid.go` — SendGrid transactional email via REST API v3
- `sms/twilio.go` — Twilio Programmable Messaging API
- `push/fcm.go` — Firebase Cloud Messaging for iOS and Android push
- `inapp/kafka.go` — Publishes in-app alert events to a Kafka topic consumed by the frontend gateway

Each adapter implements exponential backoff with jitter (3 attempts, max 30 s delay) before returning a terminal error.

### `internal/audit`

Appends delivery outcomes to the `notification_events` table. Records include the notification ID, channel, provider response code, latency, and a timestamp. This log is the source of truth for delivery reporting dashboards.

## Message Flow

A notification request travels through the following stages from ingestion to delivery:

1. An upstream service publishes a `NotificationRequest` JSON payload to the `notifications-inbound` SQS queue.
2. A consumer worker picks up the message and deserializes it into a typed struct, rejecting malformed payloads to a dead-letter queue.
3. The resolver loads recipient preferences and evaluates frequency caps. If the user has opted out or is capped, the event is recorded as `suppressed` and the SQS message is acknowledged.
4. The template engine renders the channel-specific subject and body using the request's data context.
5. The provider adapter dispatches the rendered message to the external delivery service and waits for a synchronous acknowledgement.
6. The audit component writes a `delivered` or `failed` event to the database. On failure, the message is returned to SQS for retry up to the configured maximum attempt count.
7. After the maximum retries are exhausted, the message is moved to the dead-letter queue and an alert is raised in the `#notifications-alerts` Slack channel.

## Configuration

The service is configured entirely through environment variables, which are documented in `deploy/helm/values.yaml`. Key settings:

| Variable | Default | Description |
|---|---|---|
| `SQS_QUEUE_URL` | (required) | Inbound notification queue URL |
| `CONSUMER_POOL_SIZE` | `20` | Number of concurrent SQS consumer goroutines |
| `TEMPLATE_CACHE_TTL_SECONDS` | `300` | In-memory template cache TTL |
| `MAX_DELIVERY_ATTEMPTS` | `5` | Retry limit before dead-lettering |
| `FREQ_CAP_EMAIL_PER_DAY` | `10` | Max emails per user per 24-hour window |
| `SENDGRID_API_KEY` | (required) | SendGrid authentication key |
| `TWILIO_ACCOUNT_SID` | (required) | Twilio account identifier |
| `TWILIO_AUTH_TOKEN` | (required) | Twilio authentication token |
| `FCM_SERVICE_ACCOUNT_JSON` | (required) | Firebase service account credentials (base64) |

Secrets are injected at runtime by the platform's Vault agent sidecar and are never stored in the Helm chart. Feature flags for individual channels (e.g., disabling SMS globally) are controlled via the `CHANNEL_ENABLED_*` family of boolean variables.
