---
id: PROCESS-069
type: process
title: Customer Portal Design Review Process
status: draft
owner: Director of Engineering
created: '2025-02-04T12:32:02.311Z'
updated: '2026-05-13T06:50:56.899Z'
tags:
  - process
  - customer-portal
summary: Customer Portal Design Review Process
related_standards:
  - STANDARD-049
  - STANDARD-051
related_sops:
  - SOP-087
  - SOP-090
related_systems:
  - SYSTEM-044
example: true
---

## Purpose

Ensure all Customer Portal features and UI changes are reviewed by design and engineering before shipping to customers. The design review process enforces the portal UX standard ([[STANDARD-049|STANDARD-049]]), the portal interface consistency standard ([[STANDARD-051|STANDARD-051]]), and validates accessibility, data instrumentation, and support widget integration ([[SYSTEM-044|Customer Support Widget Service]]) before a feature reaches production.

## Scope

All Customer Portal features and changes that:

- Introduce new UI components or modify existing shared components
- Add or change user flows (new pages, navigation changes, modal flows)
- Modify the portal design system tokens or component library
- Add new interactive elements (forms, modals, drawers)
- Change the information architecture (new sections, renamed navigation items)

**Out of scope:** Backend-only changes with no visible UI impact, copy/text changes to existing labels (handled via copy review), and infrastructure changes with no customer-facing effect.

## Roles and Responsibilities

- **Feature Owner** — The engineer or designer leading the feature. Responsible for: scheduling the design review, providing design mockups or Storybook previews, addressing feedback.
- **Design Reviewer** — A product designer from the portal design team. Responsible for: verifying visual consistency with the design system, checking layout and spacing, approving the final design.
- **Accessibility Reviewer** — An engineer designated as the accessibility champion for the sprint. Responsible for: running axe-core, performing keyboard navigation testing, and checking screen reader behavior on new interactive components.
- **Analytics Reviewer** — Verifies that all new user flows have `data-portal-action` attributes and that analytics events are defined in the event taxonomy before launch.
- **Support Integration Reviewer** — Required only for features that add new pages or flows where the support widget must be visible. Verifies widget placement and context pre-population are correct.

## Triggers

- A new feature PRD is approved and enters the design phase
- A significant redesign of an existing portal page is initiated
- A new component is proposed for addition to the shared component library
- The design system tokens or base styles are modified

## Inputs

- Design mockups in Figma with annotations for states (loading, empty, error)
- Storybook preview or Vercel preview deployment of the implementation
- Accessibility test results: axe-core output with zero Level A or AA violations
- List of new analytics events and `data-portal-action` values being introduced
- Confirmation that all new pages include the support widget mounting point

## Outputs

- Design review approval recorded in the feature's PR description
- Accessibility sign-off from the Accessibility Reviewer
- Analytics event names confirmed and added to the event taxonomy documentation
- Feature merged and eligible for deployment

## Steps

1. **Feature Owner** creates a design review issue in Jira linking to the Figma mockups and the PR or Storybook URL. Sets the review type (design, accessibility, analytics, support integration).
2. **Design Reviewer** reviews the Figma mockups and Storybook preview within 2 business days. Comments are added in Figma; blockers are labeled in Jira. Approves or requests changes.
3. **Feature Owner** addresses design feedback and updates the Storybook preview. Re-requests design review if changes were significant.
4. **Accessibility Reviewer** runs axe-core on the Storybook preview and the Vercel preview. Performs keyboard navigation through all interactive states. Documents findings in Jira. Approves if zero Level A or AA violations are present.
5. **Analytics Reviewer** confirms `data-portal-action` attributes are present on all new interactive elements and that event names follow the naming convention. Adds new events to the taxonomy doc.
6. **Support Integration Reviewer** (if applicable) verifies the support widget appears correctly on new pages and that any new user context (e.g., the current page or active ticket) is passed to the widget.
7. **Feature Owner** collects all approvals and marks the design review issue as resolved. Adds a "Design Reviewed" label to the PR.
8. PR is eligible for merge once Design Reviewed label is present and CI is passing.

## Controls

- PRs touching portal UI components cannot be merged without the "Design Reviewed" label
- Axe-core must run as a CI check on every portal PR; the check fails if any new Level A or AA violation is introduced
- Design review issues are retained in Jira for 12 months
- Features that bypass design review must be approved by the Director of Engineering and have a documented exception in the Jira issue
- Portal analytics event taxonomy is reviewed at the start of each sprint to incorporate new events from merged features
