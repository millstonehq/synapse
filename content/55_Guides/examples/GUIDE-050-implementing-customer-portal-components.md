---
id: GUIDE-050
type: guide
title: Implementing Customer Portal Components
status: approved
owner: Engineering Team
created: '2025-07-09T16:06:32.790Z'
updated: '2025-04-14T22:39:07.051Z'
tags:
  - guide
  - customer-portal
summary: Implementing Customer Portal Components
audience: partner
related_systems:
  - SYSTEM-042
  - SYSTEM-044
related_sops:
  - SOP-085
  - SOP-088
example: true
---

## Why Component Consistency Matters

The Customer Portal's component library is the shared language of the frontend. When every team builds the same button differently, accessibility gaps accumulate, visual inconsistency undermines brand trust, and onboarding new engineers takes longer. This guide explains how to implement components correctly — whether you're adding to the shared library or building page-level compositions.

## Using the Shared Component Library

Before implementing any UI element, check the component catalog in Storybook (`npm run storybook`) and the `src/components/ui/` directory. The library covers:

- **Form elements**: `Input`, `Select`, `Checkbox`, `RadioGroup`, `Textarea`, `Switch`
- **Feedback**: `Alert`, `Toast`, `InlineError`, `Spinner`, `Skeleton`
- **Navigation**: `Sidebar`, `Breadcrumb`, `Tabs`, `Pagination`
- **Data display**: `DataTable`, `Card`, `Badge`, `Tag`
- **Overlays**: `Modal`, `Drawer`, `Popover`, `Tooltip`

If the component you need exists in the library, use it. Do not recreate it in a feature directory.

## Adding a New Component to the Library

When the library genuinely lacks a component you need:

1. Propose the component in the `#portal-design-system` Slack channel before building; design may already have it planned
2. Start from the closest Radix UI primitive to inherit keyboard behavior and ARIA semantics for free
3. Implement the component in `src/components/ui/[component-name]/` with an `index.tsx` entry, a types file, and a test file
4. Add a Storybook story with all visual states; the story serves as living documentation
5. Open a PR tagged with `component-library` and request a review from a design system contributor

New library components require at least two reviewers: one engineer and one who can verify accessibility compliance.

## Composing Page-Level Features

Page-level components in `src/features/` may compose library components but should not contain business logic. Follow these patterns:

- Fetch data in a server component or using React Query hooks from `src/hooks/`; pass data as props to presentational components
- Wrap async operations in error boundaries; use the shared `ErrorBoundary` component from the library
- Use the `usePortalAnalytics` hook to track meaningful user interactions (button clicks, form submissions, navigation events)

## Versioning and Breaking Changes

The shared component library follows semver-like conventions:

- **Non-breaking additions** (new optional props, new variants): ship in a regular sprint
- **Breaking changes** (renamed props, removed variants, behavior changes): require a migration guide in the PR description and a deprecation period of at least one sprint
- **Deprecations**: mark with the `@deprecated` JSDoc tag and add a console warning in development mode pointing to the replacement

Never silently change the behavior of a shared component without coordination with all feature teams that use it.
