---
id: GUIDE-049
type: guide
title: Customer Portal Frontend Development Guide
status: accepted
owner: Developer Experience
created: '2025-08-22T01:45:55.306Z'
updated: '2026-03-09T00:25:19.724Z'
tags:
  - guide
  - customer-portal
summary: Customer Portal Frontend Development Guide
audience: customer
related_systems:
  - SYSTEM-044
  - SYSTEM-043
related_sops:
  - SOP-083
  - SOP-086
example: true
---

## Why This Matters

The Customer Portal is the primary surface through which customers interact with the product. Frontend code quality directly affects customer retention, accessibility compliance, and support volume. Poor frontend decisions — large bundle sizes, inaccessible components, or inconsistent error handling — create support escalations and damage trust at the moment of highest customer visibility.

This guide covers the patterns, tools, and expectations for engineers contributing to the Customer Portal frontend.

## Project Setup and Local Development

Before writing code, ensure your local environment is correctly configured:

- Clone the portal repository and install dependencies with `npm ci` (not `npm install`, which may update lockfiles)
- Copy `.env.example` to `.env.local` and fill in the development API endpoint and feature flag API key
- Run `npm run dev` to start the Next.js development server at `localhost:3000`
- Run `npm run test:watch` to start the Jest test runner in watch mode

The portal uses **Next.js** with the App Router, **TypeScript** throughout, and a shared component library built on Radix UI primitives. Familiarize yourself with the `src/components/ui/` directory before creating new components — most primitives you need already exist.

## Component Development Patterns

New components must follow these patterns:

- Build on existing design tokens from `src/styles/tokens.ts`; do not introduce hardcoded color or spacing values
- Every interactive component must be keyboard-accessible and include appropriate ARIA attributes
- Use the `useTranslation` hook for all user-visible strings; never hardcode English text in component JSX
- Add a Storybook story for each component in `src/stories/`; include stories for default, loading, error, and empty states
- Colocate component tests with the component file using the `.test.tsx` suffix

For complex state, use the portal's Zustand store slices in `src/store/`; do not introduce component-level state for data that needs to be shared across routes.

## Testing and Quality Gates

The portal CI pipeline enforces several quality gates before a PR can merge:

- **Unit tests**: Jest + React Testing Library; run with `npm test`. All new components need tests covering user interactions, not just rendering.
- **Accessibility**: `jest-axe` runs axe-core checks in the test suite; any new component with accessibility violations fails CI.
- **Type checking**: `npm run type-check` runs `tsc --noEmit`; no `any` types in component signatures.
- **Bundle analysis**: Run `npm run build:analyze` before introducing large new dependencies; PRs that increase the initial bundle by more than 10KB require a review comment explaining the tradeoff.

## Common Mistakes to Avoid

- **Direct API calls in components**: Always use the service layer in `src/services/`; never call `fetch` directly from a React component.
- **Skipping error states**: Every data-fetching component must handle loading, error, and empty states, not just the success state.
- **Hardcoded strings**: Run `npm run i18n:check` before submitting a PR; it will flag any string literals in JSX.
- **Missing focus management**: Modal dialogs, drawers, and flyouts must trap focus on open and return focus to the trigger on close.
