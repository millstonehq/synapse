---
id: STANDARD-059
type: standard
title: Billing Event Schema Standard
status: draft
owner: Head of Engineering
created: '2024-01-06T19:15:18.544Z'
updated: '2025-07-15T08:40:51.551Z'
tags:
  - standard
  - billing-engine
summary: Billing Event Schema Standard
related_policies:
  - POLICY-047
  - POLICY-050
example: true
related_systems:
  - SYSTEM-049
  - SYSTEM-050
---

## Area

This standard defines the canonical schema for all events published to the Billing Engine event bus, including subscription lifecycle events, payment events, invoice events, and usage events. It applies to any service that produces or consumes billing domain events.

A consistent event schema enables reliable event-driven integrations, simplifies audit trail reconstruction, and ensures that downstream consumers (analytics, finance, support tooling) can process billing events without per-event schema negotiation.

## Controls

- All billing events must include an `envelope` with fields: `event_id` (UUID v4), `event_type` (namespaced string, e.g. `billing.invoice.finalized`), `schema_version` (semver string), `occurred_at` (ISO 8601 UTC), and `account_id`
- Breaking schema changes (field removal, type changes) require a new `schema_version` minor or major increment and a minimum 90-day deprecation window for the old version
- Event payloads must be validated against their declared schema at publish time; events that fail schema validation must be rejected and routed to a dead-letter topic
- Sensitive fields in billing events (e.g., card last four, tax ID) must be marked with `pii: true` in the schema definition for downstream masking enforcement
- All billing event schemas must be registered in the schema registry before use in production

## Compliance Mappings

- SOC 2 CC7.1: Billing events serve as audit trail inputs and must be immutable after publication
- PCI-DSS 10.2: Payment-related events must include sufficient context to support audit log requirements
- ISO 27001 A.12.4.3: Administrator and privileged billing operations that trigger events must be traceable to individual actors

## Related Policies

- [[POLICY-047|Revenue Recognition Policy]]
- [[POLICY-050|Billing Access Control Policy]]
