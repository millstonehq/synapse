---
id: STANDARD-020
type: standard
title: Email Template Coding Standard
status: proposed
owner: Compliance Officer
created: '2024-07-20T14:01:05.877Z'
updated: '2026-06-05T22:32:24.311Z'
tags:
  - standard
  - notification-service
summary: Email Template Coding Standard
related_policies:
  - POLICY-017
  - POLICY-019
example: true
related_systems:
  - SYSTEM-020
  - SYSTEM-017
---

## Area

This standard defines requirements for authoring and maintaining HTML email templates used by the Notification Service. It applies to all email templates deployed to production, including transactional, marketing, and system alert templates.

## Controls

- All email templates must use table-based HTML layout for cross-client compatibility; CSS Grid and Flexbox are prohibited
- Templates must include a plain-text alternative (`text/plain` MIME part) alongside the HTML body
- Inline CSS must be used for all style declarations; external stylesheets and `<style>` blocks in `<head>` are not permitted
- Templates must define a `{{unsubscribe_url}}` variable and render an unsubscribe link that is visible without scrolling for non-transactional emails
- All user-provided or dynamic content must be HTML-escaped using the template engine's built-in escaping; raw interpolation is prohibited
- Images must use absolute HTTPS URLs; relative paths and embedded base64 images are prohibited
- Templates must be validated against the Litmus or Email on Acid test suite covering top 10 email clients before promotion to production

## Compliance Mappings

- CAN-SPAM Act: Section 5(a)(5) (Unsubscribe Mechanism)
- GDPR Article 7: Conditions for Consent
- SOC 2: CC8.1 (Change Management)

## Related Policies

- [[POLICY-017|Notification Opt-Out Compliance Policy]]
- [[POLICY-019|Push Notification Data Privacy Policy]]
