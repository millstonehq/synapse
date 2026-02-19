---
id: PRD-042
type: prd
title: Customer Dashboard Redesign PRD
status: draft
owner: Senior PM
created: '2025-02-07T02:10:07.341Z'
updated: '2026-05-24T12:44:25.597Z'
tags:
  - prd
  - customer-portal
summary: Customer Dashboard Redesign PRD
related_tdds:
  - TDD-044
  - TDD-041
example: true
related_standards:
  - STANDARD-051
---

## Summary

Redesign the Customer Portal dashboard to replace the existing paginated list layout with a card-based overview that surfaces actionable information above the fold, reduces Largest Contentful Paint from 3.8 seconds to under 2 seconds, and increases the percentage of customers who take a portal action within 60 seconds of login. The technical design is in [[TDD-044|TDD-044]] (search integration surfaced on the dashboard) and [[TDD-041|TDD-041]] (dashboard architecture).

## Goals

- Reduce dashboard LCP from 3.8 seconds to under 2 seconds
- Increase same-session action rate (customer performs an action within 60 seconds of login) from 38% to 55%
- Reduce "customer contacts support for information visible in the portal" ticket category by 20%
- Achieve a dashboard-specific satisfaction rating of >= 4.4 / 5.0 in post-session surveys

## In Scope

- Card-based dashboard layout with account summary, open ticket count, notification count, and account tier
- Quick-action buttons (Submit Ticket, Update Preferences, View Activity)
- Activity feed showing the 10 most recent portal events
- Integrated search bar connecting to the portal search integration
- Skeleton loading states for all async sections
- Responsive layout for mobile (34% of sessions are mobile)

## Out of Scope

- Billing summary widget (billing initiative is separate)
- Usage analytics widget (analytics team initiative)
- Customizable dashboard layout (widget reordering — future iteration)
- Push notification prompts on the dashboard

## Users and Flows

**Authenticated customers**: The primary users. They land on the dashboard after login and use it as a home base for navigating to tickets, settings, and notifications.

**First-time visitors** (post-onboarding): Customers who have just completed the onboarding wizard see a welcome card on the dashboard highlighting the top three actions. This state is shown for the first 7 days after account creation.

## Requirements

- Dashboard must load above-the-fold content (account summary StatCards) within 2 seconds P95
- StatCards must display open ticket count, unread notification count, and account tier
- Activity feed must display the 10 most recent activities with a "View All" link
- Quick-action buttons must be present for Submit Ticket, Update Preferences, and View Activity
- Search bar must be present on the dashboard and submit to the portal search results page
- Dashboard must render without JavaScript for read-only content (progressive enhancement)
- All skeleton loading placeholders must use the design system Skeleton component to prevent layout shift
- Dashboard must be responsive: StatCards display in a 1-column layout on mobile, 3-column on desktop

## KPIs

- **LCP**: P95 < 2.0 seconds on Vercel edge (measured by real user monitoring)
- **CLS**: < 0.1 Cumulative Layout Shift score
- **Same-session action rate**: >= 55% of sessions include at least one portal action within 60 seconds
- **Dashboard satisfaction**: >= 4.4 / 5.0 post-session survey rating within 30 days of launch

## Information Architecture

Dashboard documentation:

- TDD in `90_Architecture/TDDs/TDD-041` with the component architecture and GraphQL query design
- System docs for the five Customer Portal services
- This PRD defines the product requirements and success metrics

## Data Model

Dashboard data is aggregated in a single `DashboardSummary` GraphQL type:

- **DashboardSummary**: `{ account: AccountSummary, openTicketCount: Int, unreadNotificationCount: Int, recentActivity: [ActivityEvent] }`
- **AccountSummary**: `{ displayName, tier, memberSince }`
- **ActivityEvent**: `{ id, type, description, timestamp, actionUrl }`

No new persistent data model is introduced; the dashboard aggregates from existing services.

## Non-Functional

- Dashboard server component must not block render on slow API responses; implement 2-second timeout with graceful empty-state fallback
- Dashboard must be fully navigable by keyboard
- No client-side JavaScript is required to read the StatCards or activity feed; interactive elements (quick-action buttons) degrade gracefully
- Real user monitoring (RUM) must be enabled to capture LCP and CLS for every dashboard page load

## Constraints

- Must use the existing design system component library (Radix UI + Tailwind); no bespoke components except the StatCard composite
- Must use the Customer API Gateway GraphQL schema; dashboard data must be fetched in a single `DashboardSummary` query
- Budget: 2 engineers for 6 weeks
- Must not introduce a new CDN or caching layer; Vercel edge caching is the only CDN

## Risks

- **GraphQL query size** — the single `DashboardSummary` query may return too much data for customers with large activity histories. Mitigation: limit `recentActivity` to first 10 items in the page query.
- **LCP target not met** if the API Gateway P95 latency exceeds 800ms. Mitigation: instrument Gateway latency before launch; engage Platform team to add response caching if needed.
- **Design review delays** — card-based layout requires sign-off from the design team. Mitigation: use Vercel preview deployments for async design review on every PR.

## Milestones

### M1: Server component shell and StatCards (Week 1-2)

#### Deliverables

- `DashboardPage` server component with `DashboardSummary` GraphQL query
- `StatCard` components for open tickets, notifications, and account tier
- `loading.tsx` skeleton layout

#### Acceptance Criteria

- Dashboard renders StatCards with real data from the API Gateway
- Skeleton is shown while data loads; no layout shift after hydration
- LCP measured in Vercel preview at < 2.0 seconds P95

### M2: Activity Feed and Quick Actions (Week 3-4)

#### Deliverables

- `ActivityFeed` client component with initial server-side data and client-side infinite scroll
- `QuickActions` component with Submit Ticket, Update Preferences, View Activity buttons
- Search bar integration pointing to the search results page

#### Acceptance Criteria

- Activity feed shows 10 most recent items; scrolling loads the next page
- Quick-action buttons navigate to correct pages
- Search bar submits query to `/search?q=`

### M3: Responsive design, testing, and launch (Week 5-6)

#### Deliverables

- Responsive layout implemented and tested on 375px, 768px, and 1280px breakpoints
- E2E tests for dashboard render, activity feed pagination, and quick actions
- RUM enabled; LCP and CLS dashboards configured
- Staged rollout (10% → 50% → 100%) over 3 days

#### Acceptance Criteria

- Dashboard layout matches designs at all three breakpoints
- E2E test suite passes in CI
- Post-launch LCP P95 < 2.0 seconds confirmed in RUM data after 72 hours
