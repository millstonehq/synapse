---
id: WIKI-034
type: wiki
title: Customer Portal - Frontend Stack
status: deprecated
owner: Customer Team
created: '2024-12-01T18:11:29.355Z'
updated: '2025-11-12T14:36:54.733Z'
tags:
  - wiki
  - customer-portal
summary: Customer Portal - Frontend Stack
source_repo: https://git.example.com/acme/customer-portal
commit_sha: 11b6a4adbbf05a93db583a030b689dedc3de725d
generated_at: '2025-03-13T04:33:27.936Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: medium
example: true
---

## Overview

The Customer Portal front-end is built with Next.js using the App Router. It uses a hybrid rendering model: pages that require SEO or initial data (dashboard, account overview) are server-rendered; interactive widgets (notification center, support chat embed) are client components with selective hydration.

The front-end communicates exclusively with the Customer API Gateway via GraphQL using Apollo Client for cache management and optimistic UI updates.

## Framework and Rendering

The portal uses Next.js App Router with a hybrid rendering strategy:

- Server Components handle the outer layout, navigation, and initial data fetching. This keeps first-contentful-paint fast and enables server-side session validation before any HTML is sent to the browser.
- Client Components are used for interactive elements: the notification bell, preference toggles, and the support widget embed. These are hydrated on the client after the initial server render.
- Route handlers in `app/api/` proxy sensitive operations (auth token refresh, preference writes) to avoid exposing backend endpoints directly to the browser.

## State Management

Client-side state is managed with a combination of Apollo Client (for GraphQL query caching and optimistic updates) and React Context (for session state and feature flags). Server state is not duplicated in client state; components always read from Apollo cache or re-fetch rather than maintaining separate local copies.

## Component Library

The portal uses a custom internal component library built on top of Radix UI primitives with Tailwind CSS for styling. Key component families:

- **Layout**: `PortalShell`, `Sidebar`, `PageHeader` - consistent navigation structure
- **Data Display**: `DataTable`, `StatCard`, `ActivityFeed` - used across dashboard and settings pages
- **Forms**: `SettingsForm`, `TicketCreateForm` - built with React Hook Form and Zod validation
- **Feedback**: `Toast`, `InlineAlert`, `SkeletonLoader` - async state handling

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `next` | 14.x | Framework, App Router, server components |
| `@apollo/client` | 3.x | GraphQL client and cache |
| `@radix-ui/react-*` | latest | Accessible component primitives |
| `tailwindcss` | 3.x | Utility-first CSS |
| `react-hook-form` | 7.x | Form state management |
| `zod` | 3.x | Schema validation for forms and API responses |

## Build and Deployment

The portal is built as a Docker image in CI (GitHub Actions). The build step runs `next build`, which produces a standalone output directory. The image is tagged with the Git commit SHA and pushed to the container registry. ArgoCD deploys the new image to Kubernetes via a rolling update when the image tag in the Helm chart values is updated.
