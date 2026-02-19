---
id: CAPABILITY-009
type: capability
title: Warehouse Integration Capability
status: review
owner: VP Engineering
created: '2024-06-30T19:32:13.273Z'
updated: '2025-01-21T22:23:09.948Z'
tags:
  - capability
  - inventory-management
summary: Warehouse Integration Capability
evidence_links:
  - STANDARD-014
  - PROCESS-015
  - PROCESS-013
example: true
---

## Domain

- Inventory Management
- Infrastructure
- Partner Integrations

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Level 0 - Initial**: No programmatic warehouse integrations. Stock data is entered manually or via flat-file uploads on an ad hoc basis. Data is frequently stale by days.
- **Level 1 - Ad hoc**: A small number of high-priority warehouses have one-off integrations built directly without a shared framework. Each integration has different retry logic, different error handling, and different data formats.
- **Level 2 - Repeatable** (current): A warehouse adapter framework exists with standardised interfaces for webhook, polling, and EDI 846 integrations. New WMS adapters can be built using the framework in weeks rather than months. Idempotency and DLQ handling are standardised. 14 warehouse integrations are live.
- **Level 3 - Defined**: Adapter framework includes automated validation and conformance testing for new integrations. Onboarding a new WMS requires only configuration, not new code, for common protocol variants. Connector library is documented and maintained by the integrations team.
- **Level 4 - Managed**: Integration health metrics (sync lag, error rate, idempotency collision rate) are tracked per warehouse and surfaced in a merchant-facing health dashboard. SLA commitments per integration type are published.
- **Level 5 - Optimizing**: Self-healing integrations that automatically renegotiate polling intervals and batch sizes based on WMS load signals. Zero-downtime WMS credential rotation.

**Gap to Level 3**: The adapter framework supports the three primary protocols but onboarding a new WMS still requires a developer to write an adapter implementation. Declarative adapter configuration is under design. Automated conformance tests for new adapters are not yet available.

## Metrics

- Active warehouse integrations: 14 live, 3 in onboarding
- Sync lag (P95 end-to-end from WMS event to stock level update): Currently 12s, target < 15s
- Adapter error rate (events that fail after all retries): Currently 0.08%, target < 0.1%
- DLQ depth (messages awaiting manual review): 23 currently, target < 50
- Time to onboard a new WMS integration (from contract to live): Currently 6 weeks, target < 4 weeks at Level 3

## Evidence Links

- [[STANDARD-014|Warehouse Integration Protocol Standard]] - Standard defining accepted protocols, data formats, and conformance requirements for WMS integrations
- [[PROCESS-015|Warehouse Onboarding Process]] - Process for onboarding new warehouse integrations including testing, staging validation, and go-live checklist
- [[PROCESS-013|Inventory Reconciliation Process]] - Process for detecting and resolving discrepancies that arise from partial or failed sync events

## Notes

The capability advanced from Level 1 to Level 2 in Q4 2024 with the delivery of the warehouse adapter framework. The primary driver was the need to scale from 3 manually integrated warehouses to 10+ without a proportional increase in engineering effort per integration.

Key improvements needed for Level 3:
- Design and implement declarative adapter configuration so that common protocol variants (e.g., different EDI segment layouts, different webhook schemas) can be handled through configuration rather than code changes
- Build an automated conformance test suite that validates a new adapter against a set of synthetic WMS scenarios before it is promoted to production
- Publish an integration developer guide that enables the integrations team to onboard new WMS providers without core platform team involvement for standard cases
