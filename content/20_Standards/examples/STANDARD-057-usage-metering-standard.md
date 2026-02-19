---
id: STANDARD-057
type: standard
title: Usage Metering Standard
status: review
owner: Compliance Officer
created: '2025-11-21T06:45:20.431Z'
updated: '2026-02-13T08:10:33.580Z'
tags:
  - standard
  - billing-engine
summary: Usage Metering Standard
related_policies:
  - POLICY-049
  - POLICY-046
example: true
related_systems:
  - SYSTEM-050
  - SYSTEM-049
---

## Area

This standard defines requirements for the collection, validation, deduplication, and storage of usage events that drive usage-based billing. It applies to all instrumentation that emits metering events into the Billing Engine, including product APIs, background workers, and third-party integration points.

Accurate metering is the foundation of usage-based billing. This standard ensures that metered events are complete, non-duplicated, and attributable to the correct account and billing period.

## Controls

- Every usage event must include: `event_id` (UUID v4), `account_id`, `event_type`, `quantity`, `unit`, and `occurred_at` (ISO 8601 UTC timestamp)
- Usage events must be emitted idempotently; duplicate events with the same `event_id` must be deduplicated before billing aggregation
- Events must be ingested within 5 minutes of occurrence; events older than 48 hours at ingestion time must be flagged for review and not automatically billed
- Metering pipelines must achieve at least 99.9% event delivery durability, with dead-letter queues for failed events
- Usage aggregation for billing must be performed on immutable event records; post-ingestion mutation of events is prohibited

## Compliance Mappings

- SOC 2 CC4.1: Usage event logs constitute financial records and must be protected from unauthorized modification
- ASC 606: Metered usage data must support the recognition of revenue in the period performance obligations are satisfied
- ISO 27001 A.12.4.1: Metering event logs must be retained and protected as part of operational logging controls

## Related Policies

- [[POLICY-049|Invoice Retention Policy]]
- [[POLICY-046|Billing Data Accuracy Policy]]
