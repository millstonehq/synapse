---
id: ADR-0037
type: adr
title: Choose Vercel for Portal Hosting
status: approved
owner: Staff Engineer
created: '2025-07-07T22:27:28.235Z'
updated: '2026-11-27T12:45:10.361Z'
tags:
  - adr
  - customer-portal
summary: Choose Vercel for Portal Hosting
example: true
---

## Context

The Customer Portal's hosting infrastructure needed to be selected alongside the Next.js framework decision. The portal has specific requirements: global CDN distribution for 40,000 MAU across multiple regions, preview deployments for each pull request to enable design reviews, seamless Next.js integration (especially for App Router server components and edge middleware), and minimal operations overhead for a team without dedicated infrastructure engineers.

The existing portal ran on an internal Kubernetes cluster managed by the Platform team. While functional, Kubernetes deployments of Next.js required custom Docker image builds, manual CDN configuration, and no native preview deployment support. The Portal team spent an estimated 20% of engineering time on infrastructure maintenance.

Two options were evaluated: continuing with Kubernetes (internal platform) and migrating to Vercel (managed hosting).

## Decision

Host the Customer Portal on **Vercel**.

Vercel will serve as the hosting and CDN layer for the portal front-end. Deployments are triggered automatically on merge to `main` (production) and on every pull request (preview). The Customer API Gateway and backend services remain on the internal Kubernetes cluster; Vercel proxies API calls to the gateway via environment variable configuration.

## Consequences

**Positive:**
- Automatic preview deployments for every PR enable design review and UX sign-off without spinning up local environments
- Native Next.js support: App Router, server components, edge middleware, and Image Optimization work without custom configuration
- Global CDN edge network reduces static asset and server component rendering latency for international users
- Zero infrastructure maintenance overhead for the Portal team; no Kubernetes manifests, no Helm charts, no custom Docker image builds

**Negative:**
- Hosting vendor lock-in: migrating away from Vercel would require rebuilding CDN configuration, preview deployment tooling, and deployment automation
- Vercel pricing scales with team size and bandwidth; costs need to be monitored as portal traffic grows
- API calls from Vercel edge functions to the internal Kubernetes API Gateway require a secure networking path (Vercel IP allowlisting or VPN tunnel)

**Neutral:**
- The Portal team loses visibility into the underlying infrastructure; Vercel's incident status page becomes a dependency for portal availability
- Vercel's analytics and web vitals tooling provide useful data but overlap with existing internal observability tooling

## Alternatives Considered

**Continue on internal Kubernetes (Platform team managed):**
- Pro: No vendor lock-in; full control over infrastructure; co-located with backend services
- Con: No native preview deployments; Next.js App Router deployment requires custom setup; Portal team continues spending 20% of time on infrastructure
- Rejected because: The productivity gain from Vercel's managed Next.js hosting was assessed as worth the vendor lock-in risk for a customer-facing front-end.

**AWS Amplify:**
- Pro: AWS ecosystem integration, no additional vendor
- Con: Next.js support on Amplify is less mature than Vercel; App Router compatibility was limited at evaluation time; preview deployments required additional configuration
- Rejected because: Vercel's Next.js support was significantly more mature and the team had prior experience with it.
