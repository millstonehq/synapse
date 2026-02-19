---
id: REFERENCE-017
type: reference
title: WCAG 2.2 Accessibility Guidelines Reference
status: published
owner: Security Team
created: '2025-07-28T04:54:26.587Z'
updated: '2026-04-25T05:00:50.029Z'
tags:
  - reference
  - customer-portal
summary: WCAG 2.2 Accessibility Guidelines Reference
upstream_url: https://docs.example.com/wcag-2-2-accessibility-guidelines-reference
last_synced: '2025-01-24T12:37:25.724Z'
attribution: Linux Foundation
license: CC BY-SA 4.0
category: other
example: true
---

## Overview

WCAG 2.2 (Web Content Accessibility Guidelines, version 2.2) is the W3C international standard for web accessibility, published October 2023. It defines how to make web content more accessible to people with disabilities, including those with visual, auditory, physical, speech, cognitive, language, learning, and neurological disabilities.

WCAG 2.2 success criteria are organized under four principles (POUR): Perceivable, Operable, Understandable, and Robust. Each criterion has a conformance level: A (minimum), AA (standard), or AAA (enhanced). The Customer Portal is required to meet Level AA conformance.

## Conformance Levels

- **Level A**: The most basic requirements; failure causes significant barriers for some users
- **Level AA**: The standard for most legal and regulatory requirements (UK PSBAR, US Section 508, EU EN 301 549); this is the portal's required conformance level
- **Level AAA**: Enhanced requirements; not all content can meet AAA, and it is not required

## WCAG 2.2 New Success Criteria (vs 2.1)

WCAG 2.2 added nine new success criteria. The following are most relevant to the Customer Portal:

### 2.4.11 Focus Not Obscured (Minimum) — Level AA

When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content (e.g., sticky headers, modals). The portal's sticky navigation bar must not completely cover focused elements when navigating by keyboard.

**Portal implication**: Verify that sticky header height is accounted for in scroll-into-view behavior for all focusable elements.

### 2.4.12 Focus Not Obscured (Enhanced) — Level AAA

The focused component is not partially hidden (stronger than 2.4.11). This is AAA and not required, but aspirational.

### 2.5.3 Label in Name — Level A

For UI components with visible text labels, the accessible name must contain the visible text. This affects icon buttons with tooltips (e.g., the NotificationBell "Mark all read" button).

### 2.5.7 Dragging Movements — Level AA

Functionality that uses dragging motions must also be operable with a single pointer without dragging. Relevant if any portal drag-and-drop interactions are introduced.

### 2.5.8 Target Size (Minimum) — Level AA

The size of pointer input targets must be at least 24x24 CSS pixels (or have adequate spacing). Applies to all clickable elements including notification items, quick-action buttons, and toggle controls.

**Portal implication**: Audit all interactive elements in the design system for minimum 24x24 target size; update Radix UI component defaults if needed.

### 3.2.6 Consistent Help — Level A

If a mechanism for requesting help is present across multiple pages (e.g., a "Help" link in the portal nav), it must appear in the same relative location on every page.

### 3.3.7 Redundant Entry — Level A

Information that was entered by the user in the same process should not be required to be entered again unless re-entering is essential. Relevant to the multi-step onboarding wizard and ticket creation forms.

### 3.3.8 Accessible Authentication (Minimum) — Level AA

Cognitive function tests (e.g., puzzles, remembering passwords) must not be required for authentication unless an alternative is provided. CAPTCHA alternatives must be available.

**Portal implication**: Ensure that any CAPTCHA in the login or ticket submission flow has an audio alternative or other non-cognitive fallback.

## Key Principles for Portal Implementation

- **Perceivable**: All non-text content has text alternatives; minimum 4.5:1 contrast ratio for normal text (3:1 for large text); captions for any video content
- **Operable**: All functionality operable via keyboard; no keyboard traps; skip navigation links; focus indicators visible and not obscured
- **Understandable**: Page language declared; error messages identify the field and describe how to fix the error; consistent navigation
- **Robust**: Valid HTML; ARIA roles used correctly; name, role, value exposed for all custom components

## Testing Guidance

- **Automated**: Run axe-core in CI on every PR; captures approximately 30-40% of WCAG issues automatically
- **Manual keyboard test**: Tab through every new component; verify focus order, focus visibility, and keyboard activation
- **Screen reader test**: Test with NVDA + Firefox (Windows) and VoiceOver + Safari (macOS) for new interactive components
- **Color contrast**: Use the WebAIM Contrast Checker or browser DevTools to verify contrast ratios; test both light and dark mode

## Sync Notes

This reference covers the WCAG 2.2 criteria most relevant to Customer Portal development. For the full normative specification, see the upstream URL at `https://www.w3.org/TR/WCAG22/`. Re-sync this reference whenever the portal's design system or component library is updated, or when new WCAG criteria are added.
