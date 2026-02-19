---
id: WIKI-035
type: wiki
title: Customer API - Endpoint Reference
status: draft
owner: Customer Team
created: '2025-03-20T23:10:07.285Z'
updated: '2026-04-26T15:03:09.379Z'
tags:
  - wiki
  - customer-portal
summary: Customer API - Endpoint Reference
source_repo: https://git.example.com/acme/customer-api
commit_sha: d15e072c0b4e3faca91032bc6bbc726de3464334
generated_at: '2025-03-30T18:29:12.605Z'
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
importance: low
example: true
---

## Overview

The Customer API exposes a GraphQL endpoint at `/api/graphql`. All requests require a valid JWT bearer token in the `Authorization` header. The API enforces per-account rate limiting of 1000 requests/minute. This page documents the primary query and mutation types available to portal clients.

All requests should use persisted query IDs in production to reduce payload size and prevent ad-hoc query execution.

## Authentication

Every API request must include:

```
Authorization: Bearer <access_token>
```

Tokens are issued by the Identity Service with a 15-minute expiry. The portal automatically refreshes tokens using the `POST /api/auth/refresh` route handler before expiry.

## Core Queries

### `customerProfile`

Returns the authenticated customer's profile data including display name, email, tier, and account creation date.

### `preferences(namespace: String!)`

Returns all preference key-value pairs within the specified namespace (`notifications`, `display`, `communications`). Results are cached for 5 minutes.

### `supportTickets(status: TicketStatus, first: Int, after: String)`

Paginated list of the customer's support tickets. Supports cursor-based pagination. The `status` argument filters by `OPEN`, `PENDING`, `RESOLVED`, or `ALL`.

### `notificationFeed(first: Int, after: String)`

Paginated list of in-app notification events for the authenticated customer, ordered by timestamp descending.

## Core Mutations

### `updatePreference(namespace: String!, key: String!, value: String!)`

Sets a single preference value within the given namespace. Returns the updated preference object. Emits a preference change event downstream.

### `createSupportTicket(input: CreateTicketInput!)`

Creates a new support ticket with subject, body, and optional attachment references. Returns the created ticket ID and initial status.

### `markNotificationRead(notificationId: ID!)`

Marks a single notification as read. Returns the updated notification.

## Error Handling

The API uses standard GraphQL error extensions with a `code` field:

| Code | Meaning |
|------|---------|
| `UNAUTHENTICATED` | Missing or expired JWT |
| `FORBIDDEN` | Token valid but insufficient scope |
| `RATE_LIMITED` | Account rate limit exceeded |
| `NOT_FOUND` | Requested resource does not exist |
| `VALIDATION_ERROR` | Input failed schema validation |
