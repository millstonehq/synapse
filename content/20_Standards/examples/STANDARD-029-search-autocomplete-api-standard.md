---
id: STANDARD-029
type: standard
title: Search Autocomplete API Standard
status: draft
owner: Head of Engineering
created: '2024-10-30T11:59:12.043Z'
updated: '2026-07-15T18:17:23.194Z'
tags:
  - standard
  - search-platform
summary: Search Autocomplete API Standard
related_policies:
  - POLICY-022
  - POLICY-023
example: true
related_systems:
  - SYSTEM-025
  - SYSTEM-021
---

## Area

This standard defines the contract for the Search Platform's autocomplete (type-ahead) API, including request parameters, response shape, latency requirements, and suggestion source configuration. All implementations of autocomplete functionality, whether powered by Elasticsearch completion suggester, edge n-gram, or an external suggest service, must conform to this standard.

## Controls

- Autocomplete endpoints must respond within 50ms at P95 under normal load; requests exceeding 200ms must be logged as slow query events
- Suggestion responses must return a maximum of 10 suggestions per request; clients may request fewer via the `size` parameter
- Each suggestion item must include `text`, `score`, and `type` fields; additional fields are permitted but must not increase response size beyond 2KB
- Autocomplete indexes must be separate from primary search indexes to prevent suggest traffic from impacting query latency
- Suggestion sources must be configured to filter out content that fails the moderation rules defined in [[POLICY-022|Search Result Ranking Transparency Policy]]
- Autocomplete APIs must support the `highlight` parameter to return matched prefix portions for client-side rendering

## Compliance Mappings

- WCAG 2.1 AA: Success Criterion 1.3.1 (Info and Relationships) - suggestion type labels must be machine-readable
- Internal API Governance Framework v2: Section 5.3 (Latency SLO Documentation)

## Related Policies

- [[POLICY-022|Search Result Ranking Transparency Policy]]
- [[POLICY-023|Search Query Logging Policy]]
