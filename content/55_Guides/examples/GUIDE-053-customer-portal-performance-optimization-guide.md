---
id: GUIDE-053
type: guide
title: Customer Portal Performance Optimization Guide
status: review
owner: Developer Experience
created: '2025-06-01T12:19:51.801Z'
updated: '2025-02-28T15:52:09.821Z'
tags:
  - guide
  - customer-portal
summary: Customer Portal Performance Optimization Guide
audience: customer
related_systems:
  - SYSTEM-043
  - SYSTEM-044
related_sops:
  - SOP-082
  - SOP-083
example: true
---

## Understanding Portal Performance Targets

The Customer Portal has defined performance targets in the Customer Portal Performance Standard. The targets that most directly affect development decisions are:

- **LCP under 2.5s** on a 4G connection in Lighthouse
- **CLS under 0.1** across all portal pages
- **Initial JS bundle under 250KB gzipped**
- **API P95 latency under 800ms** for authenticated endpoints

This guide explains how these targets translate into day-to-day frontend development decisions.

## Bundle Size Management

JavaScript bundle size is the single biggest lever on initial load performance. Key practices:

- Run `npm run build:analyze` before adding any new dependency; the bundle analyzer shows which packages contribute to each route's size
- Use dynamic imports (`next/dynamic`) for components that are not needed on initial page load (modals, heavy data visualization, admin features)
- Prefer smaller alternatives when adding utilities: use `date-fns` functions individually rather than importing the whole library; avoid large utility libraries for tasks that can be done natively
- Check that third-party scripts and analytics are loaded with `strategy="lazyOnload"` in Next.js; marketing scripts must never block the critical rendering path

If a PR increases the initial bundle by more than 10KB, the PR description must explain the tradeoff and confirm the addition is justified.

## Image and Media Optimization

- Always use the `<Image>` component from `next/image`; it handles WebP/AVIF conversion, responsive sizes, and lazy loading automatically
- Provide the `width` and `height` props on all images to prevent layout shift (CLS impact); use `fill` only for decorative background images where dimensions are unknown
- Compress images before adding to the repository; use Squoosh or ImageOptim for one-off images; the CI pipeline enforces a 100KB limit on raw images in the `public/` directory

## React Rendering Optimization

Unnecessary re-renders waste CPU and can cause visual jank:

- Use `React.memo` for pure presentational components that receive stable props but are rendered in large lists
- Memoize expensive derived values with `useMemo`; memoize callback functions passed to child components with `useCallback`
- Use virtualization (`@tanstack/virtual`) for lists exceeding 50 items; the `DataTable` component already supports this via the `virtualized` prop
- Profile rendering with React DevTools Profiler before and after optimization; do not guess at the bottleneck

## Measuring Performance

Run Lighthouse on key portal routes weekly using `npm run lighthouse:ci`. The script generates a report in `lighthouse-reports/` and fails if any route regresses below the target thresholds. For production monitoring, Core Web Vitals are reported to Grafana via the portal's real user monitoring integration.
