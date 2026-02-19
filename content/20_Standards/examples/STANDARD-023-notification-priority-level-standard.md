---
id: STANDARD-023
type: standard
title: Notification Priority Level Standard
status: approved
owner: Security Lead
created: '2025-07-08T04:00:09.995Z'
updated: '2026-06-16T21:53:36.685Z'
tags:
  - standard
  - notification-service
summary: Notification Priority Level Standard
related_policies:
  - POLICY-017
  - POLICY-016
example: true
related_systems:
  - SYSTEM-016
  - SYSTEM-018
---

## Area

This standard defines the priority classification system used by the Notification Service to govern dispatch ordering, retry behavior, and rate limiting exemptions. It applies to all notification types across all channels.

## Controls

- Notifications must be classified into one of four priority levels: `critical`, `high`, `normal`, `low`
- `critical` notifications (security alerts, account lockouts, payment failures) are exempt from per-user rate limits and must be dispatched within 30 seconds of event receipt
- `high` priority notifications must be dispatched within 5 minutes; they consume rate limit quota but are processed before `normal` and `low` items in the queue
- `normal` priority is the default for transactional and informational messages; SLA is delivery within 15 minutes
- `low` priority is used for marketing and digest messages; they may be batched and are subject to time-of-day send windows
- Priority downgrades are permitted (e.g., retrying a failed `critical` as `high` after 24 hours) but upgrades require an explicit override approved by the on-call engineer

## Compliance Mappings

- NIST SP 800-53: SI-12 (Information Management and Retention)
- ISO 27001: A.12.4.1 (Event Logging)
- SOC 2: A1.1 (Availability Commitments)

## Related Policies

- [[POLICY-017|Notification Opt-Out Compliance Policy]]
- [[POLICY-016|Notification Delivery Guarantee Policy]]
