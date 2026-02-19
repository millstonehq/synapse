---
id: POLICY-042
type: policy
title: Customer Portal Accessibility Policy
status: approved
owner: CTO
created: '2025-02-12T03:40:45.010Z'
updated: '2026-02-18T21:03:06.064Z'
tags:
  - policy
  - customer-portal
summary: Customer Portal Accessibility Policy
example: true
related_standards:
  - STANDARD-051
  - STANDARD-049
---

## Scope

This policy governs the accessibility requirements for all user-facing features and interfaces within the Customer Portal. It applies to web pages, modal dialogs, forms, navigation components, notifications, and any interactive elements delivered to end users. All engineering contributors, designers, and QA personnel involved in Customer Portal development are covered.

## Rationale

- Legal compliance with WCAG 2.1 AA and applicable accessibility laws (ADA, Section 508, EN 301 549) reduces litigation risk
- An accessible portal expands the addressable customer base and improves usability for all users, not only those with disabilities
- Accessibility defects are significantly cheaper to fix during development than after release
- Demonstrating accessibility commitment strengthens enterprise customer procurement evaluations

## Policy Statements

- All new Customer Portal features must meet WCAG 2.1 Level AA conformance before shipping to production
- Automated accessibility scanning must be included in the CI pipeline; builds with critical violations must not be merged
- Manual accessibility testing with keyboard-only navigation and a screen reader must be performed for every new UI component
- Color contrast ratios must meet WCAG 2.1 AA minimums (4.5:1 for normal text, 3:1 for large text)
- All images, icons, and non-text content must include meaningful alternative text or be marked decorative
- Remediation of identified accessibility regressions is treated as a high-priority defect with a 5-business-day SLA

## Related Standards

- [[STANDARD-051|Customer Portal Performance Standard]]
- [[STANDARD-049|Customer Portal UI Component Standard]]
