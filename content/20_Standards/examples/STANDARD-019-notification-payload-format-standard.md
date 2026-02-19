---
id: STANDARD-019
type: standard
title: Notification Payload Format Standard
status: approved
owner: Security Lead
created: '2024-09-29T15:42:23.354Z'
updated: '2026-03-28T03:46:59.601Z'
tags:
  - standard
  - notification-service
summary: Notification Payload Format Standard
related_policies:
  - POLICY-016
  - POLICY-017
example: true
related_systems:
  - SYSTEM-016
  - SYSTEM-020
---

## Area

This standard governs the structure and encoding of all notification payloads produced and consumed by the Notification Service. It applies to the internal event schema used when services publish notification requests, as well as the canonical format used when dispatching to channel-specific providers.

## Controls

- All notification payloads must conform to the canonical JSON schema: `notification_id`, `recipient_id`, `channel`, `template_id`, `priority`, `payload`, `idempotency_key`, `created_at`
- The `idempotency_key` field is required and must be a UUID v4; dispatchers must reject payloads without a valid key
- Payload size must not exceed 4 KB for push and SMS channels; email payloads are limited to 512 KB including rendered HTML
- Channel-specific fields (e.g., `apns_topic`, `fcm_token`, `to_address`) must be nested under a `channel_context` object and must not appear at the root level
- Enum fields (`channel`, `priority`) must use lowercase snake_case values defined in the schema registry; unrecognized values must be rejected with a 422 response
- All datetime fields must use ISO 8601 UTC format

## Compliance Mappings

- NIST SP 800-53: SI-10 (Information Input Validation)
- ISO 27001: A.14.2.5 (Secure System Engineering Principles)
- SOC 2: CC6.1 (Logical Access Controls)

## Related Policies

- [[POLICY-016|Notification Delivery Guarantee Policy]]
- [[POLICY-017|Notification Opt-Out Compliance Policy]]
