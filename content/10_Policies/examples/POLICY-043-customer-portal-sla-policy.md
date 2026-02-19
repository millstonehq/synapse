---
id: POLICY-043
type: policy
title: Customer Portal SLA Policy
status: review
owner: CISO
created: '2024-12-20T18:31:19.946Z'
updated: '2025-12-06T10:26:33.904Z'
tags:
  - policy
  - customer-portal
summary: Customer Portal SLA Policy
example: true
related_standards:
  - STANDARD-049
  - STANDARD-054
---

## Scope

This policy defines the service level commitments for the Customer Portal and the obligations of the engineering team to uphold them. It covers portal availability, API response time, incident response, and planned maintenance windows. The policy applies to all components serving customer-facing traffic, including the frontend application, backend APIs, authentication services, and CDN delivery.

## Rationale

- Published SLAs set clear expectations for customers and create internal accountability for reliability
- Defined response time targets align engineering on-call behavior with business commitments
- SLA breaches trigger contractual remedies; proactive monitoring reduces their frequency and financial impact
- Clear maintenance window policies allow customers to plan around portal downtime

## Policy Statements

- The Customer Portal must maintain a minimum monthly uptime of 99.5% excluding approved maintenance windows
- API P95 response time must not exceed 800ms for authenticated portal requests under normal load
- P1 incidents (portal fully unavailable) must have an on-call response within 15 minutes of alert firing
- Planned maintenance must be communicated to customers at least 48 hours in advance via status page and in-portal banner
- SLA performance must be reported to the product and engineering leadership monthly with incident root cause summaries
- All SLA breaches must be documented with a postmortem within 5 business days

## Related Standards

- [[STANDARD-049|Customer Portal UI Component Standard]]
- [[STANDARD-054|Customer Portal Accessibility Standard]]
