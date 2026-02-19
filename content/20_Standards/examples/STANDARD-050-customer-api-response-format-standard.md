---
id: STANDARD-050
type: standard
title: Customer API Response Format Standard
status: draft
owner: Security Lead
created: '2024-05-14T03:55:46.843Z'
updated: '2026-04-04T18:49:31.229Z'
tags:
  - standard
  - customer-portal
summary: Customer API Response Format Standard
related_policies:
  - POLICY-042
  - POLICY-045
example: true
related_systems:
  - SYSTEM-042
  - SYSTEM-044
---

## Area

This standard defines the structure, naming conventions, and error format for all HTTP API responses served to the Customer Portal frontend. It applies to REST endpoints consumed by the portal, including authentication, account management, data retrieval, and action endpoints. Consistency in response format reduces frontend parsing complexity and makes error handling predictable.

## Controls

- All successful responses must use HTTP 2xx status codes and return a JSON body with a top-level `data` key containing the response payload
- Error responses must use appropriate 4xx or 5xx status codes and return a JSON body with `error.code` (machine-readable string), `error.message` (human-readable), and `error.requestId` fields
- Paginated list responses must include a top-level `pagination` object with `total`, `page`, `pageSize`, and `hasMore` fields
- Response bodies must not include internal stack traces, database error messages, or server hostnames in any environment
- Date-time fields must be formatted as ISO 8601 strings in UTC; clients are responsible for timezone conversion
- API responses must set appropriate `Cache-Control` headers; authenticated responses must include `no-store`

## Compliance Mappings

- OWASP API Security Top 10: API3 (Excessive Data Exposure) - responses must only include fields the requesting role is authorized to see
- SOC 2 CC6.1: Access controls enforced at response layer by role-based field filtering
- Internal [[POLICY-042|Customer Portal Accessibility Policy]] (error messages must be human-readable for display in accessible UI components)

## Related Policies

- [[POLICY-042|Customer Portal Accessibility Policy]]
- [[POLICY-045|Customer Portal Third-Party Integration Policy]]
