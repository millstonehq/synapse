---
id: WIKI-036
type: wiki
title: Customer Portal - Design System
status: accepted
owner: Customer Team
created: '2024-07-26T20:30:23.546Z'
updated: '2026-12-21T08:51:58.432Z'
tags:
  - wiki
  - customer-portal
summary: Customer Portal - Design System
source_repo: https://git.example.com/acme/customer-portal
commit_sha: c33735dce849c03681baac9df7614e1ecdaa4bb4
generated_at: '2025-06-04T17:09:47.215Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4
importance: medium
example: true
---

## Overview

The Customer Portal Design System is the shared visual and interaction language used across all portal pages and the embedded support widget. It is built on Radix UI primitives with Tailwind CSS utility classes and provides accessible, consistent UI components to all teams contributing to the portal.

The design system is published as an internal npm package (`@acme/portal-ui`) and versioned independently from the portal application. Teams should pin to a specific minor version and upgrade deliberately.

## Architecture

The design system is organized into three tiers:

- **Tokens**: CSS custom properties for color, spacing, typography, and shadow. Tokens are the source of truth for all visual values. Changing a token propagates to all components that reference it.
- **Primitives**: Low-level unstyled components from Radix UI (Dialog, Popover, Select, etc.). These handle accessibility semantics and keyboard interactions without imposing visual style.
- **Components**: Opinionated, styled components built on top of primitives. These are the building blocks used directly in portal pages.

## Key Components

- **`Button`**: Primary, secondary, destructive, and ghost variants. Supports loading state with spinner overlay. Follows WCAG 2.2 focus-visible requirements.
- **`DataTable`**: Sortable, paginated table component. Accepts a column definition array and a data array. Supports row selection and inline actions.
- **`StatCard`**: Dashboard metric display showing a label, primary value, and trend indicator (up/down/neutral with percentage).
- **`SettingsForm`**: Wrapper component that integrates React Hook Form with Zod schema validation and displays field-level error messages.
- **`Toast`**: Non-blocking notification component. Stacked at the bottom-right. Auto-dismisses after 5 seconds; can be dismissed manually.

## Configuration

Design tokens are defined in `packages/portal-ui/src/tokens.css` as CSS custom properties. To override tokens for theming:

```css
:root {
  --color-brand-primary: #0057b8;
  --color-brand-secondary: #f5a623;
}
```

Dark mode is supported via the `data-theme="dark"` attribute on the `<html>` element.

## Dependencies

| Package | Purpose |
|---------|---------|
| `@radix-ui/react-*` | Accessible component primitives |
| `tailwindcss` | Utility classes for component styling |
| `class-variance-authority` | Variant-based className composition |
| `lucide-react` | Icon set used throughout the portal |
