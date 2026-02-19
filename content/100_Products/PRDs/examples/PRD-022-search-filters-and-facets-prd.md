---
id: PRD-022
type: prd
title: Search Filters and Facets PRD
status: deprecated
owner: Senior PM
created: '2025-10-20T03:48:42.407Z'
updated: '2026-08-20T21:24:11.156Z'
tags:
  - prd
  - search-platform
summary: Search Filters and Facets PRD
related_tdds:
  - TDD-021
  - TDD-025
example: true
related_standards:
  - STANDARD-028
---

## Summary

Add faceted filtering to the search experience so users can narrow results by structured dimensions such as content type, category, date range, and tags. Facets appear as a sidebar panel with result counts per filter option, allowing progressive refinement without losing context. This initiative is grounded in the query parser work in [[TDD-021|TDD-021]] and the aggregation design in [[TDD-025|TDD-025]].

Note: This PRD is marked deprecated. The faceted search feature was absorbed into the AI-Powered Search Experience PRD (PRD-021) and implemented as part of that initiative.

## Goals

- Enable users to filter search results by at least 6 structured facet dimensions
- Reduce time-to-relevant-result by providing guided refinement
- Decrease zero-click rate for faceted searches by 15% vs. unfaceted baseline

## In Scope

- Facet dimensions: content type, category, publish date range, author, tags, reading time
- Facet counts displayed alongside filter options (showing how many results each option contains)
- Multi-select facets (user can apply multiple values within a dimension with OR logic)
- Active filter chips displayed in the search results header for easy removal
- URL-serializable filter state for shareability and browser history support
- Facet configuration managed by the search team via DynamoDB (no code deploy needed)
- Compliance with [[STANDARD-028|STANDARD-028]] for filter parameter naming conventions

## Out of Scope

- Hierarchical (nested) facets
- Facet-specific sorting within each dimension
- Saved filters or filter presets per user
- Facets on vector/semantic search results (keyword-only facets in this release)

## Users and Flows

**Browse-intent users** arrive at search results and are uncertain about which specific result they want. Facets help them narrow from "articles about machine learning" to "tutorials published in the last 6 months." These users benefit most from category and date facets.

**Known-domain users** already know what type of content they want (e.g., "show me only API reference docs"). They use content-type facets to immediately filter out irrelevant result types. These users value fast, keyboard-accessible filter application.

**Content operators** configure which facet dimensions are active and their display order via the DynamoDB facet configuration table, without needing a deployment.

## Requirements

- Facet counts must be computed using Elasticsearch `post_filter` to remain stable as filters are applied
- Total bucket count across all active facets in a single request must not exceed 500 (circuit breaker enforcement per TDD-025)
- Facet configuration changes take effect within 5 minutes (DynamoDB-backed config with refresh)
- Filter state must serialize to URL query parameters for shareable URLs
- Applying a filter must not cause a full page reload; results and facets update in place
- Facet results cached in Redis for 60 seconds per unique (query, filter combination)
- [[STANDARD-028|STANDARD-028]] parameter naming conventions applied to all filter URL parameters

## KPIs

- **Filter usage rate**: Target > 25% of search sessions use at least one filter
- **Zero-click rate (faceted searches)**: Target 15% lower than unfaceted baseline
- **Facet load latency**: P95 facets response within 200ms (must not add latency vs. unfaceted search)

## Information Architecture

- Technical design: TDD-025 (Faceted Aggregation), TDD-021 (Query Parser)
- Facet configuration: DynamoDB `search-query-config` table, managed by Search team
- Dashboard: Kibana `search-facets-*` index pattern for filter usage metrics

## Data Model

- **FacetConfig**: field name, aggregation type, max buckets, label, enabled flag — stored in DynamoDB
- **FilterState**: map of facet_id to selected values — serialized in URL query parameters
- **FacetGroup**: facet_id, label, list of buckets (value, count, is_selected) — returned in API response

## Non-Functional

- Facet computation must not increase P95 query latency by more than 25ms
- Facet cache must use Redis with 60-second TTL to reduce Elasticsearch aggregation load
- Bucket size circuit breaker must prevent runaway aggregation requests

## Constraints

- Must use existing Elasticsearch aggregation framework; no external faceting service
- Facet dimensions limited to keyword and date fields (no full-text fields)
- Must not require changes to the existing search URL structure (backward compatible)

## Risks

- **Coordinating node CPU pressure** from large aggregations (documented in REPORT-037). Mitigation: bucket size guard and Redis caching reduce aggregation frequency.
- **Facet count staleness** for rapidly changing content. Mitigation: 60-second cache is acceptable; counts are approximate by design.

## Milestones

### M1: Backend Aggregation API (Weeks 1-3)

#### Deliverables

- Facet aggregation API endpoint with post_filter support
- Bucket size guard and circuit breaker implemented
- Redis caching layer deployed

#### Acceptance Criteria

- Facet counts returned correctly for all 6 configured dimensions
- P95 latency not increased by more than 25ms vs. unfaceted baseline

### M2: Frontend Integration and GA (Weeks 4-6)

#### Deliverables

- Facet sidebar UI component with multi-select support
- URL filter serialization implemented
- Filter usage analytics instrumented

#### Acceptance Criteria

- Filter state survives page reload via URL parameters
- Filter usage rate measured and above 10% in initial cohort
