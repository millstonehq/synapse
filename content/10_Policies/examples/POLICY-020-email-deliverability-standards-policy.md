---
id: POLICY-020
type: policy
title: Email Deliverability Standards Policy
status: review
owner: VP Engineering
created: '2025-08-09T13:17:26.427Z'
updated: '2026-07-23T06:46:21.376Z'
tags:
  - policy
  - notification-service
summary: Email Deliverability Standards Policy
example: true
related_standards:
  - STANDARD-022
  - STANDARD-024
---

## Scope

This policy applies to all outbound email sent by the Notification Service, including transactional emails, marketing campaigns, and system alerts. It covers the engineering, marketing, and product teams that author or trigger email sends, as well as the email sending infrastructure and third-party providers.

## Rationale

- Poor email deliverability directly reduces user engagement and causes missed critical communications
- ISP and mailbox provider filtering algorithms penalize senders with high bounce and complaint rates, affecting the entire sending domain
- DMARC, DKIM, and SPF authentication are prerequisites for inbox placement and protection against phishing abuse of company domains
- Deliverability incidents can result in domain blacklisting, which requires days or weeks to remediate

## Policy Statements

- All production email sending domains must have valid SPF, DKIM, and DMARC records configured and passing before any email is sent
- Hard bounce rate must remain below 2%; soft bounce rate must remain below 5% measured over any rolling 7-day window
- Spam complaint rate must remain below 0.1% as reported by email provider feedback loops
- Email sending IPs must be warmup-scheduled when introduced or after any significant sending gap; cold-start blasts are prohibited
- All list segments used for marketing emails must be scrubbed against the suppression list before each send
- Email infrastructure configuration changes (DNS, sending IP, provider switch) require a senior engineer review before execution

## Related Standards

- [[STANDARD-022|SMS Gateway Integration Standard]]
- [[STANDARD-024|In-App Message Format Standard]]
