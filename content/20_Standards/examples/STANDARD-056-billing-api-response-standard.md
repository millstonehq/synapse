---
id: STANDARD-056
type: standard
title: Billing API Response Standard
status: review
owner: Compliance Officer
created: '2024-06-24T07:09:54.842Z'
updated: '2025-02-23T18:59:32.193Z'
tags:
  - standard
  - billing-engine
summary: Billing API Response Standard
related_policies:
  - POLICY-048
  - POLICY-050
example: true
related_systems:
  - SYSTEM-050
  - SYSTEM-047
---

## Area

This standard defines the required response shapes, error formats, status codes, and pagination conventions for all Billing Engine API endpoints. It applies to the public billing REST API and any internal billing service APIs consumed by other platform services.

Consistent API responses reduce integration effort, improve error handling reliability, and enable predictable behavior across billing consumers.

## Controls

- All successful billing API responses must return HTTP 200 with a JSON body containing a `data` envelope and a `meta` object with at minimum `request_id` and `timestamp`
- Billing API error responses must use RFC 7807 Problem Details format with fields: `type`, `title`, `status`, `detail`, and `instance`
- Paginated list endpoints must support cursor-based pagination using `cursor` and `limit` query parameters; `next_cursor` must be included in responses where more pages exist
- Monetary amount fields in API responses must be represented as integers in the smallest currency unit (e.g., cents for USD) alongside a `currency` field containing the ISO 4217 code
- Billing API endpoints must include idempotency key support via the `Idempotency-Key` request header for all write operations

## Compliance Mappings

- OWASP API Security Top 10: API3 (Broken Object Level Authorization) — all billing objects must be scoped to the authenticated account
- SOC 2 CC7.2: Monitoring for unauthorized API access patterns must be enforced at the billing API gateway layer
- PCI-DSS 6.5: Billing API responses must not expose raw card data in any field

## Related Policies

- [[POLICY-048|Billing Dispute Resolution Policy]]
- [[POLICY-050|Billing Access Control Policy]]
