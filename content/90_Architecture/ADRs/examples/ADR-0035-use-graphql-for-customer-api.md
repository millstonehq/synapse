---
id: ADR-0035
type: adr
title: Use GraphQL for Customer API
status: draft
owner: Staff Engineer
created: '2024-01-30T14:56:43.212Z'
updated: '2026-11-29T12:53:44.399Z'
tags:
  - adr
  - customer-portal
summary: Use GraphQL for Customer API
example: true
---

## Context

The Customer API Gateway needed to expose data from multiple backend services (Preference Service, Support Widget Service, Analytics Service) to the portal front-end. The existing portal used five separate REST endpoints for the dashboard page alone, requiring five round-trips on page load. This contributed to the poor performance profile of the legacy portal.

The team needed an API style that could aggregate data from multiple backend services in a single request, enable the front-end to fetch exactly the fields it needs (avoiding over-fetching), and support a schema-first development workflow where the front-end and back-end teams could agree on the contract before implementation started.

The gateway team was small (3 engineers) and needed a solution with strong tooling support for schema validation, code generation, and documentation.

## Decision

Adopt **GraphQL** (via Apollo Server) as the API style for the Customer API Gateway.

The gateway will implement a schema-stitched GraphQL API that aggregates types from backend services. Frontend teams use persisted queries in production to prevent ad-hoc query execution. The schema is the source of truth for the front-end/back-end contract; schema changes require review approval from both teams before merging.

## Consequences

**Positive:**
- Single round-trip for multi-service data fetches significantly reduces dashboard page load time
- Field-level selection eliminates over-fetching; mobile clients send and receive smaller payloads
- Schema-first development enables front-end and back-end teams to work in parallel against a shared contract
- Strong TypeScript code generation tooling (GraphQL Code Generator) removes manual type maintenance

**Negative:**
- GraphQL caching is more complex than REST: standard HTTP cache headers do not apply to POST requests; requires persisted queries and CDN configuration workarounds
- N+1 query problem requires DataLoader implementation for any field that fetches per-item from a backend service
- Learning curve for engineers unfamiliar with GraphQL; schema design requires careful thought to avoid breaking changes

**Neutral:**
- The GraphQL schema adds a layer of indirection between the front-end and the underlying REST APIs of backend services
- Schema stitching requires the gateway to be updated when backend services add new types or fields

## Alternatives Considered

**REST with BFF (Backend for Frontend):**
- Pro: Simpler caching, well-understood by all engineers, no schema overhead
- Con: BFF layer for each client type adds maintenance burden; N+1 call patterns return as dashboard feature complexity grows
- Rejected because: The aggregation requirements for the dashboard page were complex enough that a REST BFF would have become a GraphQL gateway without the schema benefits.

**tRPC:**
- Pro: Full-stack TypeScript type safety without a separate schema definition step
- Con: Requires TypeScript on both client and server; does not support native mobile clients or third-party integrations; less mature ecosystem
- Rejected because: The Customer Portal may need to expose APIs to non-TypeScript clients in the future; tRPC's TypeScript coupling was too constraining.
