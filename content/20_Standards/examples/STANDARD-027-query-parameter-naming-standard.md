---
id: STANDARD-027
type: standard
title: Query Parameter Naming Standard
status: approved
owner: Head of Engineering
created: '2025-11-02T04:09:17.100Z'
updated: '2026-05-07T09:14:55.730Z'
tags:
  - standard
  - search-platform
summary: Query Parameter Naming Standard
related_policies:
  - POLICY-025
  - POLICY-024
example: true
related_systems:
  - SYSTEM-023
  - SYSTEM-024
---

## Area

This standard defines the naming conventions for all HTTP query parameters accepted by the Search Platform's query APIs, including the primary search endpoint, autocomplete endpoint, and facet count endpoint. Consistent parameter naming reduces integration friction for API consumers and enables shared query parsing middleware across services.

## Controls

- Query string parameters must use `snake_case` naming; camelCase and kebab-case are not permitted
- The main search term parameter must be named `q` for all search endpoints; aliases such as `query`, `search`, or `keyword` are not acceptable
- Pagination parameters must be named `cursor` (for cursor-based pagination) or `from`/`size` (for offset-based, only when explicitly approved)
- Filter parameters must follow the pattern `filter[field_name]` for exact match filters and `range[field_name][gte|lte]` for range filters
- Sort parameters must be named `sort` with value format `field:asc` or `field:desc`; multi-sort must use repeated `sort` parameters
- Boolean flags must use values `true`/`false` (lowercase); `1`/`0` or `yes`/`no` are not acceptable

## Compliance Mappings

- Internal API Governance Framework v2: Section 3.1 (Parameter Naming Conventions)
- OpenAPI 3.1 parameter specification: all parameters must be documented in the service's OpenAPI spec

## Related Policies

- [[POLICY-025|Search Infrastructure Scaling Policy]]
- [[POLICY-024|Search Content Moderation Policy]]
