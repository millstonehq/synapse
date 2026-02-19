---
id: STANDARD-021
type: standard
title: Push Notification Schema Standard
status: review
owner: Head of Engineering
created: '2024-02-25T00:11:12.777Z'
updated: '2025-01-11T11:31:34.353Z'
tags:
  - standard
  - notification-service
summary: Push Notification Schema Standard
related_policies:
  - POLICY-020
  - POLICY-016
example: true
related_systems:
  - SYSTEM-019
  - SYSTEM-017
---

## Area

This standard specifies the schema requirements for push notification payloads sent to iOS (APNs) and Android (FCM) platforms via the Notification Service. It ensures consistency, platform compliance, and safe handling of device tokens and notification content.

## Controls

- Push payloads must include required fields: `title` (max 65 chars), `body` (max 240 chars), `notification_id`, `deep_link`, and `channel_context.device_token`
- The `badge` count field must only be set for iOS payloads; Android payloads must use `notification.badge` per FCM spec
- Payloads must not include raw PII; user context required for personalization must be resolved server-side before dispatch
- The `priority` field must map to platform equivalents: `critical` → APNs `time-sensitive` / FCM `high`, `normal` → APNs `active` / FCM `normal`
- Device tokens must be validated against a format regex before dispatch; invalid tokens must be discarded and the associated record marked for cleanup
- Schema version must be included in every payload as `schema_version`; consumers must reject payloads with unsupported versions

## Compliance Mappings

- NIST SP 800-53: SC-8 (Transmission Confidentiality and Integrity)
- ISO 27001: A.14.1.3 (Protecting Application Services Transactions)
- GDPR Article 32: Security of Processing

## Related Policies

- [[POLICY-020|Email Deliverability Standards Policy]]
- [[POLICY-016|Notification Delivery Guarantee Policy]]
