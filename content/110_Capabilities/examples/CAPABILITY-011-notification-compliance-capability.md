---
id: CAPABILITY-011
type: capability
title: Notification Compliance Capability
status: accepted
owner: Head of Engineering
created: '2024-11-15T14:48:57.281Z'
updated: '2026-11-26T15:59:40.945Z'
tags:
  - capability
  - notification-service
summary: Notification Compliance Capability
evidence_links:
  - PROCESS-022
  - PROCESS-023
  - STANDARD-024
example: true
---

## Domain

- CAN-SPAM, GDPR, and CASL compliance for commercial email notifications
- One-click and link-based unsubscribe enforcement across all email templates
- Opt-out signal propagation to routing engine and suppression lists
- Audit trail for preference changes and unsubscribe events for regulatory reporting
- Consent record retention and data subject access request (DSAR) support

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Unsubscribe enforcement**: 4/5 - One-click List-Unsubscribe header is present in all emails; link-based unsubscribe token is validated and enforced; global, category, and channel-level scopes are supported
- **Opt-out propagation**: 3/5 - Preference changes propagate to routing engine within 30 seconds via RabbitMQ event; suppression list updates are synchronous for hard bounces but asynchronous (up to 5 minutes) for user-initiated unsubscribes
- **Audit trail**: 3/5 - `preference_events` table captures all preference changes with timestamp, scope, and actor; audit records are retained for 24 months but automated compliance reporting is not yet implemented
- **Consent management**: 2/5 - Opt-in consent is collected at registration but stored in the user service, not the notification service; no formal consent record linkage for GDPR Article 7 documentation

**Gap to Level 4**: Implement automated compliance reports from the audit trail, reduce unsubscribe propagation latency to under 5 seconds, and establish formal consent record linkage.

## Metrics

- Unsubscribe processing time: median 320ms from click to preference update (target < 500ms)
- Opt-out propagation to routing engine: median 18 seconds (target < 30 seconds)
- Suppression list coverage: 100% of hard-bounce and unsubscribe events captured
- Audit record retention compliance: 100% of `preference_events` retained for 24 months
- DSAR response time: currently manual, average 3 days (target < 72 hours with partial automation)

## Evidence Links

- [[PROCESS-022|Notification Compliance Audit Process]] - Quarterly review of opt-out handling, audit trail completeness, and suppression list accuracy
- [[PROCESS-023|Channel Opt-Out Compliance Process]] - Operational steps for propagating opt-out signals across all delivery channels
- [[STANDARD-024|Notification Compliance Standard]] - Defines CAN-SPAM, GDPR, and CASL requirements applicable to notification content and delivery

## Notes

- The consent management gap (Level 2) is the highest compliance risk; a cross-team initiative with the identity team is planned for Q4 to link consent records to notification preferences
- One-click List-Unsubscribe (RFC 8058) is verified by a pre-publish template validator that blocks publishing any email template missing the required header
