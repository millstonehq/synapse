---
id: GUIDE-069
type: guide
title: Customer Portal Component Library Guide
status: draft
owner: Engineering Team
created: '2025-07-27T19:15:43.011Z'
updated: '2026-02-20T01:00:03.709Z'
tags:
  - guide
  - customer-portal
summary: Customer Portal Component Library Guide
audience: customer
related_systems:
  - SYSTEM-043
  - SYSTEM-045
related_sops:
  - SOP-083
  - SOP-084
example: true
---

## Why This Matters

The Customer Portal uses a shared component library built on Radix UI and Tailwind CSS. Using the component library instead of building custom components from scratch ensures visual consistency, accessibility compliance, and reduced duplication. This guide explains how to use the library effectively and how to contribute new components.

The portal's analytics and preference tracking capabilities (used by [[SYSTEM-043|Customer Preference Service]] and [[SYSTEM-045|Customer Analytics Service]]) depend on consistent data attribute patterns on components — another reason not to bypass the library with ad-hoc HTML.

## The Mental Model

The component library has three layers:

1. **Design Tokens**: CSS variables for colors, spacing, typography, and border radii — the raw values from the design system
2. **Primitive Components**: Unstyled, accessible primitives from Radix UI (Dialog, Dropdown, Tooltip, etc.)
3. **Composed Components**: Portal-specific components built on top of Radix primitives with Tailwind styling applied (StatCard, NotificationItem, SearchResult, etc.)

When you need a UI element:
- First check if a composed component already exists
- If not, build on a Radix primitive and add Tailwind classes
- Only create a new composed component if the element will be reused across more than two places

## Using Existing Components

Components are imported from `@portal/ui`:

```tsx
import { StatCard, NotificationItem, SkeletonCard } from '@portal/ui'
import { Button, Badge, Dialog } from '@portal/ui/primitives'
```

### StatCard

Used in the dashboard to display a key metric:

```tsx
<StatCard
  label="Open Tickets"
  value={openTicketCount}
  trend={{ direction: 'down', percent: 12 }}
  icon={<TicketIcon />}
/>
```

Props: `label` (string), `value` (number | string), `trend` (optional), `icon` (optional ReactNode), `loading` (boolean — shows skeleton).

### SkeletonCard

Use for all loading states to prevent layout shift. Always match the skeleton dimensions to the final component:

```tsx
// In loading.tsx
<SkeletonCard height={120} width="100%" />
```

### NotificationItem

Renders a single notification row in the Notification Center panel:

```tsx
<NotificationItem
  id={notification.id}
  title={notification.title}
  body={notification.body}
  isRead={notification.isRead}
  category={notification.category}
  timestamp={notification.createdAt}
  onMarkRead={handleMarkRead}
/>
```

## Data Attributes for Analytics

All interactive components in the library emit a `data-portal-action` attribute on click events. The Customer Analytics Service collects these attributes to build usage funnels. When building new composed components, include `data-portal-action` on the primary clickable element:

```tsx
<button data-portal-action="quick_action_submit_ticket" onClick={handleClick}>
  Submit Ticket
</button>
```

The attribute value format is `{context}_{action}` (snake_case). See the analytics event taxonomy in the Customer Analytics capability for a list of defined action names.

## Adding a New Component

Follow these steps when adding a new composed component:

1. Check Radix UI (https://www.radix-ui.com/primitives) for a suitable primitive; prefer using a Radix primitive over a raw HTML element for anything interactive
2. Create the component in `packages/ui/src/components/YourComponent.tsx`
3. Add a Storybook story in `packages/ui/src/stories/YourComponent.stories.tsx`
4. Run `npx axe-core` on the Storybook story to check for accessibility violations before submitting a PR
5. Add `data-portal-action` attributes to all interactive elements
6. Export the component from `packages/ui/src/index.ts`
7. Reference [[SYSTEM-043|Customer Preference Service]] integration points in the component README if the component reads or writes preferences

For detailed steps on publishing a new component version, see the component library publishing SOP.

## Dark Mode

The portal supports dark mode via the `data-theme="dark"` attribute on the root `<html>` element (set by the Preference Service). All design tokens have dark-mode variants defined in `packages/ui/src/tokens/dark.css`. When creating new components, use token CSS variables (e.g., `--color-surface-1`) rather than hardcoded Tailwind color classes to ensure correct dark-mode behavior.

## Common Questions

### "Can I use a third-party component that's not in the library?"

Check with the design team first. Third-party components that ship their own CSS may conflict with the portal's design tokens and dark mode. If approved, wrap the third-party component in a composed portal component so the integration point is one file.

### "How do I override the styles of a library component?"

Pass a `className` prop to extend or override Tailwind classes. Do not use inline styles. If you find yourself frequently overriding the same classes, the component API probably needs a new variant prop — open an issue on the component library repo.

### "The Radix primitive I need isn't wrapped yet. What do I do?"

Use the raw Radix primitive directly with Tailwind classes for your feature. Once you've found the right API surface, extract it to a composed component following the steps above. Don't ship unstyled Radix primitives in application code.
