---
id: REFERENCE-018
type: reference
title: Next.js App Router API Reference
status: published
owner: Engineering Team
created: '2025-12-15T08:44:40.023Z'
updated: '2025-02-12T03:24:25.657Z'
tags:
  - reference
  - customer-portal
summary: Next.js App Router API Reference
upstream_url: https://docs.example.com/next-js-app-router-api-reference
last_synced: '2025-10-17T12:07:34.027Z'
attribution: Linux Foundation
license: CC BY-SA 4.0
category: documentation
example: true
---

## Overview

The Next.js App Router (introduced in Next.js 13, stabilized in 14) is a file-system-based router built on React Server Components. It replaces the legacy Pages Router with a layout-centric architecture where components default to server-side rendering and client-side interactivity is opt-in. The Customer Portal uses Next.js 14 with the App Router as its primary framework.

This reference summarizes the App Router APIs used in the portal codebase and documents patterns and constraints specific to our implementation. For the full Next.js documentation, see the upstream URL.

## Directory Structure Conventions

```
app/
  layout.tsx          - Root layout: applies the portal shell (nav, footer, auth gate)
  page.tsx            - Index route: redirects authenticated users to /dashboard
  dashboard/
    page.tsx          - Dashboard page (server component)
    loading.tsx       - Skeleton shown by React Suspense during data fetch
    error.tsx         - Error boundary for the dashboard route segment
  settings/
    page.tsx          - Settings page (server component for initial data)
  tickets/
    page.tsx          - Ticket list (server component)
    [id]/
      page.tsx        - Ticket detail (server component, dynamic segment)
  search/
    page.tsx          - Search results page
```

## Server vs. Client Components

By default, all components in the `app/` directory are **Server Components**. They run on the server and never ship JavaScript to the client. Use Server Components for:
- Layout structure
- Initial data fetching (GraphQL queries)
- Static content that does not need interactivity

Add `'use client'` at the top of a file to mark it as a **Client Component**. Client Components are pre-rendered on the server and hydrated on the client. Use Client Components for:
- Event handlers (`onClick`, `onChange`, `onSubmit`)
- React hooks (`useState`, `useEffect`, `useRef`)
- Apollo Client hooks (`useQuery`, `useMutation`, `useSubscription`)
- Browser APIs (localStorage, WebSocket, IntersectionObserver)

**Portal rule**: Never add `'use client'` to a component unless it requires interactivity or browser APIs. Keep the client bundle lean.

## Data Fetching Patterns

### Server Component fetch (GraphQL)

```tsx
// app/dashboard/page.tsx — Server Component
import { getClient } from '@/lib/apollo/server'
import { DASHBOARD_QUERY } from '@/lib/graphql/generated'

export default async function DashboardPage() {
  const { data } = await getClient().query({ query: DASHBOARD_QUERY })
  return <DashboardShell data={data.dashboardSummary} />
}
```

The portal uses `@apollo/experimental-nextjs-app-support` to provide a per-request Apollo Client instance in Server Components. Do not import the client-side `ApolloClient` instance in Server Components.

### loading.tsx (Suspense boundary)

Next.js automatically wraps a route segment in a React `<Suspense>` boundary and shows `loading.tsx` while the server component's async data fetch resolves. All data-fetching pages in the portal must have a corresponding `loading.tsx` with skeleton placeholders.

### error.tsx (Error boundary)

`error.tsx` must be a Client Component (`'use client'`). It receives an `error` prop and a `reset` function. The portal uses a standard `ErrorBoundary` component from the design system for all `error.tsx` files.

## Routing API

- `redirect(url)` — Redirect from a Server Component (throws internally; do not wrap in try/catch)
- `notFound()` — Render the nearest `not-found.tsx` from a Server Component
- `useRouter()` — Client Component hook for programmatic navigation
- `usePathname()` — Client Component hook to read the current URL path
- `useSearchParams()` — Client Component hook to read query string parameters; wrap in `<Suspense>` when used in a page-level component

## Metadata API

Each page can export a `metadata` object or a `generateMetadata` async function to set `<head>` tags:

```tsx
export const metadata = {
  title: 'Dashboard — Customer Portal',
  description: 'View your account summary and recent activity',
}
```

Use `generateMetadata` when the title depends on fetched data (e.g., a ticket detail page).

## Portal-Specific Conventions

- All authenticated routes must re-validate the session JWT in the root `layout.tsx` before rendering child routes; use `auth()` from the portal auth library
- Never call `cookies()` or `headers()` in a component that is intended to be statically cached
- Apollo Client cache must not be shared between requests in Server Components; use the per-request client instance

## Sync Notes

This reference covers App Router APIs as of Next.js 14. Re-sync when the portal upgrades to a new Next.js major version. Key areas to check on upgrade: async Server Component patterns, caching behavior changes (`fetch` cache semantics), and new Router Cache configurations.
