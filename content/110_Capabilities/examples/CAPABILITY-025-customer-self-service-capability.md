---
id: CAPABILITY-025
type: capability
title: Customer Self-Service Capability
status: approved
owner: VP Engineering
created: '2024-02-14T05:43:51.517Z'
updated: '2026-05-29T16:18:01.418Z'
tags:
  - capability
  - customer-portal
summary: Customer Self-Service Capability
evidence_links:
  - PROCESS-054
  - PROCESS-051
  - STANDARD-049
example: true
---

## Domain

- Customer Portal
- Product
- Self-Service

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No self-service capability. Customers must contact support for all account management tasks.
- **Level 1 - Ad hoc**: Basic account viewing available but most actions require a support ticket or phone call. No structured self-service portal.
- **Level 2 - Repeatable**: Customers can update basic profile information and view their ticket history. Self-service coverage is partial; complex tasks still require support contact.
- **Level 3 - Defined** (current): Comprehensive self-service portal with ticket submission, preference management, password change, and MFA enrollment. Self-service flows are documented in standards and follow a defined design process.
- **Level 4 - Managed**: Self-service deflection rate is measured and tracked against targets. Automated alerting when deflection rate drops below threshold. Regular user research informs self-service improvements.
- **Level 5 - Optimizing**: AI-assisted self-service (intelligent article suggestions, chat bot first-line resolution). Proactive self-service nudges based on account health signals. Deflection rate > 50%.

**Gap to Level 4**: Deflection rate tracking is manual today. Need to instrument self-service completion events in the analytics pipeline and configure automated reporting.

## Metrics

- Self-service deflection rate: Currently 20%, target 30%
- Tier-1 support ticket volume per 1,000 MAU: Currently 38, target < 27
- Portal task completion rate: Currently 72%, target 85%
- Median time to first portal action (new customers): Currently 8 minutes, target < 3 minutes
- WCAG 2.2 Level AA violation count: Currently 3, target 0

## Evidence Links

- [[PROCESS-054|Portal Self-Service Onboarding Process]] - Process for onboarding customers to portal self-service features
- [[PROCESS-051|Customer Account Recovery Process]] - Process for handling account access recovery via self-service
- [[STANDARD-049|Customer Portal UX Standard]] - UX and accessibility standards governing portal self-service flows

## Notes

The Customer Portal team reached Level 3 in Q1 2025 with the launch of the redesigned dashboard, ticket management, and settings pages.

Key work required for Level 4:
- Instrument analytics events for all major self-service flows (ticket submission, preference save, password change)
- Build a self-service metrics dashboard visible to the Portal PM and engineering lead
- Set up automated alerting if the deflection rate falls below 20% in any rolling 7-day window
- Resolve the remaining 3 WCAG 2.2 AA violations identified in the Q1 2025 accessibility audit
