---
id: STANDARD-052
type: standard
title: Customer Portal Internationalization Standard
status: review
owner: Head of Engineering
created: '2025-10-21T00:17:36.878Z'
updated: '2026-04-23T15:10:24.608Z'
tags:
  - standard
  - customer-portal
summary: Customer Portal Internationalization Standard
related_policies:
  - POLICY-044
  - POLICY-042
example: true
related_systems:
  - SYSTEM-042
  - SYSTEM-041
---

## Area

This standard defines the requirements for internationalizing the Customer Portal to support multiple languages, locales, and regional formats. It applies to all user-visible strings, date and number formatting, text directionality, locale-aware sorting, and translation management workflows. Any feature that introduces new user-visible text must comply with this standard from the initial implementation.

## Controls

- All user-visible strings must be externalized into locale resource files; hardcoded strings in component code are not permitted
- The translation key namespace must reflect the feature area (e.g., `account.profile.title`); generic or ambiguous keys are not permitted
- Date, time, currency, and number formatting must use the platform's i18n library locale-aware formatters; manual string formatting is not permitted
- The portal must support RTL text layout for Arabic and Hebrew locales; new layout components must be tested in RTL mode
- New locale resource files must go through a professional translation review before shipping; machine-only translations require a native speaker sign-off
- Missing translation keys must fall back to the base locale (en-US) and generate a monitoring alert in non-production environments

## Compliance Mappings

- WCAG 2.1 SC 3.1.1: Language of Page - each page must declare its language in the HTML `lang` attribute
- EN 301 549 Clause 9.3.1: Language identification requirements for accessible internationalized content
- Internal [[POLICY-042|Customer Portal Accessibility Policy]] (locale changes must not break accessible component behavior)

## Related Policies

- [[POLICY-044|Customer Content Moderation Policy]]
- [[POLICY-042|Customer Portal Accessibility Policy]]
