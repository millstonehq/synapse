---
id: STANDARD-024
type: standard
title: In-App Message Format Standard
status: approved
owner: Security Lead
created: '2025-09-19T19:47:00.611Z'
updated: '2025-05-25T00:07:51.728Z'
tags:
  - standard
  - notification-service
summary: In-App Message Format Standard
related_policies:
  - POLICY-017
  - POLICY-016
example: true
related_systems:
  - SYSTEM-016
  - SYSTEM-017
---

## Area

This standard defines the format requirements for in-app messages delivered by the Notification Service to web and mobile clients via the real-time notification feed. It covers message structure, rendering constraints, and dismissal tracking.

## Controls

- In-app message payloads must include: `notification_id`, `title` (max 80 chars), `body` (max 300 chars), `action_url` (optional), `icon_type` (enum), `expires_at`, `dismissible` (boolean)
- The `icon_type` enum must use predefined values from the design system token set; custom icon URLs are not permitted
- Action URLs must use relative paths within the application or approved deep-link schemes; arbitrary external URLs require a security review
- Rendered HTML in message body is not permitted; plain text only, with newlines rendered as line breaks
- In-app messages must include a client-side acknowledgment event (viewed, clicked, dismissed) that is sent back to the Notification Service for delivery confirmation
- Messages with `expires_at` in the past must be silently discarded by the client without display

## Compliance Mappings

- NIST SP 800-53: SI-10 (Information Input Validation)
- ISO 27001: A.14.2.5 (Secure System Engineering Principles)
- WCAG 2.1 AA: Success Criterion 1.4.3 (Contrast Minimum)

## Related Policies

- [[POLICY-017|Notification Opt-Out Compliance Policy]]
- [[POLICY-016|Notification Delivery Guarantee Policy]]
