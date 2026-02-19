---
id: STANDARD-053
type: standard
title: Customer Portal Error Handling Standard
status: draft
owner: Compliance Officer
created: '2025-12-28T14:23:37.799Z'
updated: '2026-06-26T07:06:29.709Z'
tags:
  - standard
  - customer-portal
summary: Customer Portal Error Handling Standard
related_policies:
  - POLICY-043
  - POLICY-042
example: true
related_systems:
  - SYSTEM-042
  - SYSTEM-044
---

## Area

This standard governs how errors are detected, communicated, and logged throughout the Customer Portal. It applies to frontend error boundaries, API error responses, form validation errors, network failure handling, and backend exception management. Consistent error handling reduces customer confusion during failures and ensures operations teams have the information needed for rapid diagnosis.

## Controls

- The frontend must implement React error boundaries at the page and feature-section level; unhandled errors must display a user-friendly fallback UI, not a blank screen or raw exception
- All API errors must be caught by the portal's global HTTP client and mapped to user-facing messages using the approved error message catalog; raw API error strings must not be displayed to customers
- Form validation errors must be associated with their triggering input via `aria-describedby`; error messages must appear inline adjacent to the field, not only in a summary banner
- All frontend exceptions must be reported to the error tracking platform (Sentry) with session context; PII must be scrubbed before reporting
- Backend services must log errors with structured fields: `timestamp`, `requestId`, `service`, `level`, `message`, and relevant context; stack traces must only appear in `debug` level logs
- HTTP 500-level errors must not leak internal implementation details in the response body

## Compliance Mappings

- WCAG 2.1 SC 3.3.1: Error Identification - errors must be described in text
- WCAG 2.1 SC 3.3.3: Error Suggestion - where possible, portal must suggest how to fix validation errors
- OWASP Top 10 A05: Security Misconfiguration - error responses must not disclose stack traces or server details

## Related Policies

- [[POLICY-043|Customer Portal SLA Policy]]
- [[POLICY-042|Customer Portal Accessibility Policy]]
