---
id: POLICY-017
type: policy
title: Notification Opt-Out Compliance Policy
status: approved
owner: CTO
created: '2025-06-08T06:21:16.091Z'
updated: '2025-02-21T15:18:21.072Z'
tags:
  - policy
  - notification-service
summary: Notification Opt-Out Compliance Policy
example: true
related_standards:
  - STANDARD-023
  - STANDARD-022
---

## Scope

This policy applies to all marketing, promotional, and non-transactional notification channels managed by the Notification Service, including email newsletters, push notifications, and SMS campaigns. It covers all engineers, product managers, and third-party integrations that send notifications to end users.

## Rationale

- CAN-SPAM, CASL, and GDPR require honoring opt-out requests within defined timeframes or face regulatory penalties
- User trust depends on reliable suppression of unwanted communications — ignoring opt-outs increases spam complaints and damages sender reputation
- Email providers (SendGrid, SES) impose deliverability penalties when complaint rates exceed thresholds
- Maintaining a global suppression list prevents re-enrollment through alternative channels or flows

## Policy Statements

- All marketing and promotional notifications must include a clearly accessible, one-click unsubscribe mechanism
- Opt-out requests must be processed and take effect within 10 business days for email, and immediately for SMS and push
- A global suppression list must be maintained across all notification channels; unsubscribing from one channel must not re-enable another without explicit user consent
- Hard bounces and spam complaint events from email providers must automatically add recipients to the suppression list
- Re-subscribing a previously opted-out user requires affirmative double opt-in confirmation
- Suppression list records must be retained for a minimum of 3 years for compliance audits

## Related Standards

- [[STANDARD-023|Notification Priority Level Standard]]
- [[STANDARD-022|SMS Gateway Integration Standard]]
