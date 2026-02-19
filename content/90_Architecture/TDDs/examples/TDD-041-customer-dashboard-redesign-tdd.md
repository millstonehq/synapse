---
id: TDD-041
type: tdd
title: Customer Dashboard Redesign TDD
status: accepted
owner: Senior Engineer
created: '2025-05-30T10:44:19.129Z'
updated: '2026-09-05T12:14:55.552Z'
tags:
  - tdd
  - customer-portal
summary: Customer Dashboard Redesign TDD
related_adrs:
  - ADR-0034
  - ADR-0035
example: true
---

## Summary

Redesign the Customer Portal dashboard to improve first-load performance, reduce cognitive load, and surface the most actionable information to customers. The redesign replaces the existing paginated list layout with a card-based overview that combines account health summary, recent activity, and quick actions. This TDD covers the front-end architecture and data layer for the redesigned dashboard, implementing the requirements from [[ADR-0034|ADR-0034]] and [[ADR-0035|ADR-0035]].

## Overview

The redesigned dashboard uses Next.js server components for the initial render, with selective client component hydration for interactive elements (activity feed, quick-action buttons). Data is fetched from the Customer API Gateway via a single GraphQL query that aggregates account, support, and notification data in one round-trip.

Key design principles:
- **Single query per page load**: The dashboard GraphQL query fetches all above-the-fold data in one request to minimize round-trips
- **Server-first rendering**: Static structure and non-personalized content render on the server; personalized widgets hydrate on the client
- **Progressive enhancement**: The page is usable with JavaScript disabled for read-only content
- **Skeleton loading**: All async sections show skeleton placeholders while data is loading, preventing layout shift

## Architecture

- **Shell Component** (server): `DashboardPage` — fetches the GraphQL query server-side, passes data to child components. No client JS on this component.
- **StatCards Component** (server): Renders key metrics (open tickets, notification count, account tier) from prefetched data.
- **ActivityFeed Component** (client): Infinite-scroll feed of recent portal activity. Fetches initial items server-side; subsequent pages fetched client-side on scroll.
- **QuickActions Component** (client): Contextual action buttons (Submit Ticket, Update Preferences, View Invoice) with optimistic UI on click.
- **NotificationBell Component** (client): Reuses the existing notification center component; integrated via shared state.

## Information Model

- **DashboardSummary**: `{ account: AccountSummary, openTicketCount: Int, unreadNotificationCount: Int, recentActivity: [ActivityEvent] }`
- **AccountSummary**: `{ displayName: String, tier: CustomerTier, memberSince: Date }`
- **ActivityEvent**: `{ id: ID, type: ActivityType, description: String, timestamp: DateTime, actionUrl: String }`

## Interfaces

- `query DashboardPage { dashboardSummary { account { displayName tier } openTicketCount unreadNotificationCount recentActivity(first: 10) { ... } } }` — primary page query
- `query ActivityFeedPage($after: String!) { recentActivity(first: 20, after: $after) { ... } }` — pagination query for infinite scroll
- `mutation MarkActivityRead(id: ID!)` — marks an activity item as read

## Files and Layout

```
app/
  dashboard/
    page.tsx              - Server component, GraphQL query, passes data to widgets
    loading.tsx           - Skeleton loading state (shown by Next.js Suspense)
    DashboardShell.tsx    - Layout: StatCards + ActivityFeed + QuickActions
components/
  dashboard/
    StatCard.tsx          - Server component, displays a single metric
    ActivityFeed.tsx      - Client component, infinite scroll activity list
    QuickActions.tsx      - Client component, contextual action buttons
lib/
  graphql/
    dashboard.graphql     - GraphQL query definitions
    generated/            - TypeScript types generated from schema
```

## Work Plan

1. **Phase 1 - GraphQL schema extension (Week 1)**: Add `dashboardSummary` type to the Customer API Gateway schema; implement resolvers; update TypeScript types
2. **Phase 2 - Server component shell (Week 2)**: Implement `DashboardPage` server component with data fetching; implement `StatCard` components; add `loading.tsx` skeleton
3. **Phase 3 - Activity feed (Week 3)**: Implement `ActivityFeed` client component with infinite scroll; implement pagination query
4. **Phase 4 - Quick actions (Week 3-4)**: Implement `QuickActions` component with optimistic UI; integrate with existing ticket and preference flows
5. **Phase 5 - Testing and polish (Week 4)**: E2E tests for dashboard page; performance measurement (LCP, CLS targets); accessibility review

## Risks and Mitigations

- **Risk**: Single GraphQL query returns too much data for some customers (e.g., very large activity feeds). **Mitigation**: Limit `recentActivity` to first 10 items in the page query; remaining items fetched on demand.
- **Risk**: Server component data fetch latency delays first paint if the API Gateway is slow. **Mitigation**: Add a 2-second timeout with graceful degradation to empty state if the query times out.
- **Risk**: Infinite scroll ActivityFeed causes layout shift on load. **Mitigation**: Reserve fixed height for the feed container; use skeleton placeholders until data arrives.
