---
id: POLICY-019
type: policy
title: Push Notification Data Privacy Policy
status: proposed
owner: VP Engineering
created: '2025-02-14T05:37:11.784Z'
updated: '2026-02-18T11:22:14.771Z'
tags:
  - policy
  - notification-service
summary: Push Notification Data Privacy Policy
example: true
related_standards:
  - STANDARD-020
  - STANDARD-021
---

## Scope

This policy applies to all push notification workflows that collect, process, or transmit user device tokens, notification content, and delivery metadata. It covers the Notification Service, mobile clients, and any vendor integrations (e.g., APNs, FCM) used for push delivery.

## Rationale

- Device tokens are considered personal data under GDPR and must be handled with the same controls as other PII
- Push notification payloads may inadvertently contain sensitive user data if templates are not reviewed before deployment
- Vendor transmission of push payloads to APNs/FCM creates a data processor relationship requiring contractual controls
- Device token leakage could enable unauthorized targeting or user fingerprinting

## Policy Statements

- Device tokens must be stored encrypted at rest and must not be logged in plaintext in application or infrastructure logs
- Push notification payloads must not contain sensitive personal data (account numbers, passwords, health data, full names combined with financial context)
- Device tokens must be invalidated and removed within 30 days of a user revoking push notification consent or deleting their account
- All push notification vendor contracts must include a Data Processing Agreement (DPA) before integration goes live
- Push delivery metadata (token, timestamp, delivery status) must be retained no longer than 90 days unless required for compliance purposes
- Any new data field added to push payloads must undergo a privacy review before deployment

## Related Standards

- [[STANDARD-020|Email Template Coding Standard]]
- [[STANDARD-021|Push Notification Schema Standard]]
