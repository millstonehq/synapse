---
id: ADR-0034
type: adr
title: Choose Next.js for Customer Portal
status: review
owner: Staff Engineer
created: '2024-09-10T19:22:26.412Z'
updated: '2026-08-09T18:51:53.783Z'
tags:
  - adr
  - customer-portal
summary: Choose Next.js for Customer Portal
example: true
---

## Context

The Customer Portal team needed to choose a front-end framework for the new customer-facing web application. Requirements included server-side rendering for performance and SEO on key public-facing pages (login, help center), a strong TypeScript ecosystem, good developer experience for a team of 4-6 engineers, and the ability to host on Vercel or Kubernetes.

The existing portal was a client-side-only React SPA built with Create React App, which resulted in poor Largest Contentful Paint scores (avg 3.8s) and no server-side rendering capability. The redesign was an opportunity to choose a modern framework that addressed these gaps. The team evaluated React frameworks with file-based routing and SSR support.

The Customer Portal serves approximately 40,000 monthly active users with diverse device capabilities. Mobile users (34% of sessions) on slower connections were disproportionately affected by the SPA's bundle size. Server-rendered HTML with selective hydration was a core requirement for the replacement.

## Decision

Adopt **Next.js 14** with the App Router as the front-end framework for the Customer Portal.

The portal will use server components for layout, navigation, and initial data fetching. Client components will be used only for interactive elements (notification bell, support widget, preference toggles). All API calls from server components will go through the Customer API Gateway using persisted GraphQL queries.

## Consequences

**Positive:**
- Server components enable fast first-contentful paint without JS bundle overhead for non-interactive pages
- App Router file-based routing reduces boilerplate and aligns with team experience
- Built-in image optimization and font optimization improve Core Web Vitals out of the box
- Strong TypeScript integration and large ecosystem of compatible libraries

**Negative:**
- App Router is newer than Pages Router; some third-party libraries do not yet have full App Router compatibility
- Server component mental model requires discipline to avoid client/server boundary mistakes
- Build times are longer than CRA for large projects; incremental builds needed

**Neutral:**
- Hosting on Kubernetes requires a custom Docker image build; not as seamless as Vercel but fully supported
- The React server component model is a paradigm shift for engineers familiar with purely client-side React

## Alternatives Considered

**Remix:**
- Pro: Strong server-rendering story, nested layouts, built-in form handling
- Con: Smaller ecosystem than Next.js, fewer engineers with Remix experience on the team
- Rejected because: Team familiarity strongly favored Next.js; Remix advantages did not outweigh the learning curve cost for the team composition.

**Nuxt.js (Vue):**
- Pro: Excellent DX, strong SSR support
- Con: Vue, not React; entire component library and team would need to switch ecosystems
- Rejected because: The team and existing component library are React-based; switching to Vue was not in scope.

**SvelteKit:**
- Pro: Excellent performance, small bundle sizes
- Con: Very small team, limited TypeScript ecosystem maturity at the time of evaluation
- Rejected because: Ecosystem maturity and team familiarity concerns outweighed the performance advantages.
