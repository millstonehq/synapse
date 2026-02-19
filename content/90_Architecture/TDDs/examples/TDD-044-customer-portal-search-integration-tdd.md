---
id: TDD-044
type: tdd
title: Customer Portal Search Integration TDD
status: deprecated
owner: Principal Engineer
created: '2025-01-01T01:38:49.993Z'
updated: '2025-02-21T00:10:06.411Z'
tags:
  - tdd
  - customer-portal
summary: Customer Portal Search Integration TDD
related_adrs:
  - ADR-0037
  - ADR-0035
example: true
---

## Summary

Design the full-text search integration for the Customer Portal, enabling customers to search across their support tickets, help center articles, notification history, and account activity from a single search bar. The integration connects the portal frontend to an Elasticsearch-backed search service exposed through the Customer API Gateway GraphQL schema as specified in [[ADR-0035|ADR-0035]], hosted and deployed via Vercel as described in [[ADR-0037|ADR-0037]].

## Overview

Search is the top-requested feature in the Customer Satisfaction Survey. The current portal requires customers to navigate to individual sections to find information. The new search integration provides a unified, scoped search experience with instant results and keyboard navigation.

Key design principles:
- **Scoped search**: Results are partitioned by content type (tickets, help articles, activity); the customer can filter by scope
- **Security-first**: All search queries are scoped to the authenticated customer's data; cross-customer data leakage is prevented by prefixing all queries with `customer_id`
- **CDN-safe**: Search queries use persisted query IDs; results are not cached at the CDN layer (Cache-Control: no-store) to prevent data exposure
- **Keyboard-accessible**: The search command palette supports full keyboard navigation (arrow keys, Enter, Escape) per WCAG 2.2

## Architecture

- **SearchBar Component** (client): A `cmdk`-based command palette mounted in the portal shell; debounces input at 300ms before issuing a GraphQL query
- **search resolver** (Customer API Gateway): Fans out to the Elasticsearch search service with a scoped query; returns a unified `SearchResultSet` with typed result variants
- **Elasticsearch index**: Separate indices per content type (`portal_tickets`, `portal_help_articles`, `portal_activity`); all documents include a `customer_id` field used as a mandatory filter term
- **Index sync jobs**: CDC consumers that subscribe to ticket and activity events and write to Elasticsearch; help article index is refreshed on CMS publish

## Information Model

- **SearchResultSet**: `{ query: String, totalCount: Int, results: [SearchResult] }`
- **SearchResult**: union of `TicketResult | HelpArticleResult | ActivityResult`
- **TicketResult**: `{ id: ID, subject: String, status: TicketStatus, updatedAt: DateTime, url: String }`
- **HelpArticleResult**: `{ id: ID, title: String, excerpt: String, url: String }`
- **ActivityResult**: `{ id: ID, description: String, timestamp: DateTime, url: String }`

## Interfaces

- `query PortalSearch($query: String!, $scope: SearchScope, $first: Int) { portalSearch(query: $query, scope: $scope, first: $first) { totalCount results { __typename ... on TicketResult { id subject status } ... on HelpArticleResult { id title excerpt } ... on ActivityResult { id description timestamp } } } }` — primary search query
- `SearchScope` enum: `ALL | TICKETS | HELP | ACTIVITY`

## Files and Layout

```
components/
  search/
    SearchBar.tsx           - Client component: cmdk command palette, debounced input
    SearchResult.tsx        - Presentational: single result row with type icon
    SearchResultGroup.tsx   - Presentational: grouped results by scope
lib/
  graphql/
    search.graphql          - Query and fragment definitions
    generated/              - Generated TypeScript types
  hooks/
    usePortalSearch.ts      - Apollo lazy query hook with debounce
services/
  search-indexer/
    ticket-consumer.ts      - CDC consumer: indexes ticket events
    activity-consumer.ts    - CDC consumer: indexes activity events
    help-sync.ts            - CMS webhook handler: syncs help articles
```

## Work Plan

1. **Phase 1 - Elasticsearch setup (Week 1)**: Provision Elasticsearch cluster; define index mappings for tickets, help articles, activity; implement initial index population job
2. **Phase 2 - GraphQL schema (Week 2)**: Add `portalSearch` query to Customer API Gateway; implement resolver with scope-based fan-out; enforce customer_id filter
3. **Phase 3 - Frontend (Week 3)**: Build `SearchBar` command palette; connect to GraphQL query; implement keyboard navigation and accessibility
4. **Phase 4 - Index sync (Week 4)**: Implement CDC consumers for ticket and activity events; implement help article CMS webhook
5. **Phase 5 - Testing and performance (Week 5)**: Load test search at 50 concurrent queries; E2E test for all three scope types; verify no cross-customer data leakage

## Risks and Mitigations

- **Risk**: Elasticsearch query exposes another customer's data if the `customer_id` filter is omitted by a bug. **Mitigation**: Add a mandatory filter term injection at the resolver level that is not overridable by the frontend query; add a security integration test that asserts queries without a valid customer session return zero results.
- **Risk**: Index sync lag means newly created tickets do not appear in search results immediately. **Mitigation**: Disclose in the UI that search results update within 30 seconds; CDC consumer processes events with a target latency of under 10 seconds.
- **Risk**: Elasticsearch cold-start latency on first query of the day. **Mitigation**: Implement a synthetic warm-up query on deployment; route to a replica shard for read traffic.
