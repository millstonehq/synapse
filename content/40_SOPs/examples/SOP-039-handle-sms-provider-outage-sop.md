---
id: SOP-039
type: sop
title: Handle SMS Provider Outage SOP
status: approved
owner: DevOps Lead
created: '2025-05-08T11:29:02.458Z'
updated: '2025-07-08T07:47:13.916Z'
tags:
  - sop
  - notification-service
summary: Handle SMS Provider Outage SOP
related_process: PROCESS-020
related_systems:
  - SYSTEM-019
example: true
---

## Preconditions

- The `sms_delivery_rate_low` or `sms_gateway_timeout` alert has fired, or there is a report of widespread SMS non-delivery
- You have confirmed the outage is provider-side (not a Notification Service configuration error)
- The Platform Lead and on-call engineer have been notified
- The secondary SMS provider is configured and credentials are accessible in the secrets manager

## Materials/Access

- Primary SMS provider status page and support contact
- Secondary SMS provider (Vonage or equivalent) credentials in the secrets manager
- Notification Service routing configuration access to switch active SMS provider
- Monitoring dashboard with SMS delivery rate and error rate panels
- Slack access to `#notifications-incidents`

## Procedure

1. Post in `#notifications-incidents`: "SMS provider outage detected. Provider: [primary]. Delivery rate: [current %]. Starting failover assessment."
2. Confirm the outage is provider-side by checking the primary provider's status page for an active incident affecting SMS delivery.
3. Check the Notification Service logs for the provider error responses (e.g., `503 Service Unavailable`, gateway timeout) to confirm the failure mode.
4. Notify the Platform Lead and request approval to initiate failover to the secondary provider.
5. Update the Notification Service SMS routing configuration to set the secondary provider as active.
6. Trigger a test SMS to a known valid number to confirm the secondary provider is accepting sends.
7. Verify on the monitoring dashboard that delivery rate recovers within 5 minutes of switching providers.
8. Monitor the secondary provider for 30 minutes to confirm stable delivery before stepping away.
9. When the primary provider resolves their incident, schedule reversion during a low-volume period following the same verification steps.

## Validation

- SMS delivery rate has returned above 95% on the monitoring dashboard
- Test SMS delivered successfully via the secondary provider
- No error rate spikes on the secondary provider after 30 minutes of traffic
- Primary provider status page shows the incident as resolved (pre-reversion)

## Rollback

1. If the secondary provider also fails after failover, evaluate whether SMS can be suspended temporarily and critical notifications rerouted to email or push.
2. Notify affected stakeholders that SMS delivery is suspended and communicate expected resolution timeline.
3. Contact both providers' support lines simultaneously to expedite resolution.
4. Resume SMS delivery on whichever provider recovers first, following the validation steps.
