---
id: STANDARD-054
type: standard
title: Customer Portal Accessibility Standard
status: approved
owner: Head of Engineering
created: '2024-08-11T11:15:44.712Z'
updated: '2025-03-16T15:04:19.122Z'
tags:
  - standard
  - customer-portal
summary: Customer Portal Accessibility Standard
related_policies:
  - POLICY-041
  - POLICY-043
example: true
related_systems:
  - SYSTEM-041
  - SYSTEM-042
---

## Area

This standard specifies the technical implementation requirements for accessibility across the Customer Portal. It translates the WCAG 2.1 AA conformance requirement from policy into concrete engineering controls covering semantic HTML, ARIA usage, keyboard interaction patterns, focus management, color and motion, and automated testing integration. All portal engineers are expected to apply these controls when building or modifying portal features.

## Controls

- All interactive elements (buttons, links, form controls) must be implemented with native HTML elements where possible; custom interactive widgets must implement the appropriate ARIA design pattern from the ARIA Authoring Practices Guide
- Focus order must follow a logical reading sequence; `tabindex` values greater than 0 are prohibited
- Modal dialogs must trap focus when open and return focus to the triggering element on close
- Animated content (auto-playing carousels, loading spinners, transitions) must respect the `prefers-reduced-motion` media query
- Color must never be the sole means of conveying information; icons, text labels, or patterns must accompany color-coded states
- Automated accessibility checks using axe-core must be integrated into the component test suite; components must pass all critical and serious violations before merging

## Compliance Mappings

- WCAG 2.1 AA: Full conformance required for all customer-facing portal pages
- ADA Title III / Section 508: Federal accessibility requirements applicable to software serving US customers
- EN 301 549 v3.2.1: European accessibility standard aligning with WCAG 2.1

## Related Policies

- [[POLICY-041|Customer Data Privacy Policy]]
- [[POLICY-043|Customer Portal SLA Policy]]
