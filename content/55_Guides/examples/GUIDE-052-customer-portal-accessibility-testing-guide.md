---
id: GUIDE-052
type: guide
title: Customer Portal Accessibility Testing Guide
status: approved
owner: Developer Experience
created: '2024-06-29T09:45:31.036Z'
updated: '2025-11-08T10:21:39.571Z'
tags:
  - guide
  - customer-portal
summary: Customer Portal Accessibility Testing Guide
audience: customer
related_systems:
  - SYSTEM-042
  - SYSTEM-043
related_sops:
  - SOP-089
  - SOP-083
example: true
---

## Why Accessibility Testing Is Your Responsibility

Automated accessibility tools catch roughly 30-40% of WCAG violations. The remaining 60-70% require human judgment: Does this screen reader announcement make sense? Is this keyboard interaction pattern intuitive? Can a user with motor impairments complete this form without a mouse? As the engineer who built the feature, you are the first line of accessibility testing.

This guide covers the automated tools integrated into the CI pipeline and the manual testing practices expected before every PR.

## Automated Testing with axe-core

The portal test suite includes `jest-axe` which runs axe-core checks on rendered components. Any new component test should include an axe assertion:

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

Automated checks will catch: missing alt text, missing form labels, insufficient color contrast, and basic ARIA misuse. They will not catch: logical reading order issues, confusing focus order, or misleading screen reader announcements.

## Keyboard Navigation Testing

Before submitting a PR, test your feature using only the keyboard (no mouse):

- `Tab` and `Shift+Tab` must move focus through all interactive elements in a logical order
- `Enter` must activate buttons and links; `Space` must activate buttons and checkboxes
- `Escape` must close modal dialogs, drawers, and popovers and return focus to the trigger
- `Arrow keys` must navigate within composite widgets (menus, tabs, radio groups, listboxes)
- No focus traps except within modal dialogs (where trapping focus is correct behavior)

If any of the above fail, the PR must not be submitted until they are fixed.

## Screen Reader Testing

Test with at least one screen reader before marking a feature ready for review:

- **macOS/iOS**: VoiceOver (built-in, activated with `Cmd+F5` on macOS)
- **Windows**: NVDA (free) with Chrome or Firefox

Key things to verify with a screen reader:
- All images have meaningful alt text or are marked `aria-hidden="true"` if decorative
- Form fields announce their label, type, and any validation errors when focused
- Dynamic content updates (toasts, inline errors appearing after form submission) are announced via `aria-live` regions
- Loading states announce when they start and when content is ready

## Using the Browser DevTools Accessibility Panel

Chrome DevTools' Accessibility panel (Elements > Accessibility) shows the accessibility tree for any selected element. Use it to verify that ARIA roles, labels, and states are being communicated correctly. Pay particular attention to custom interactive components where you've manually applied ARIA attributes.
