---
id: MEETING-024
type: meeting
title: SKU Management Redesign Kickoff
status: approved
owner: Product Manager
created: '2025-12-12T12:54:17.057Z'
updated: '2026-02-24T07:39:18.900Z'
tags:
  - meeting
  - inventory-management
summary: SKU Management Redesign Kickoff
company: InventoryManagement
topic: SKU Management Redesign Kickoff
meeting_date: '2024-04-09T01:18:26.873Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: SKU Management Platform Redesign
- **Topic**: SKU Management Redesign Kickoff
- **Date/Time**: 2024-04-09 9:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Platform Engineer, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Kickoff for the SKU management redesign project. The current SKU registry is a flat table with no native support for product variants, bundles, or international catalog structures. Redesign is required before Q3 global expansion.

## Observations by Domain

- **Current Architecture**: The SKU registry is a single monolithic table with 2.1M records; variant and bundle relationships are encoded in free-text description fields rather than structured parent-child records
- **International Requirements**: Global expansion requires locale-specific SKU aliases, multi-UOM configurations, and market-specific regulatory attribute fields
- **Performance**: P95 SKU lookup latency has reached 85ms against a 20ms target; index strategy needs a redesign for the current data volume
- **Naming Conventions**: Existing naming convention standard does not accommodate multi-market variant codes; standard update is a prerequisite for implementation
- **Migration Risk**: 8 downstream services have direct dependencies on the current SKU schema; a phased dual-write migration approach is preferred

## Key Metrics & Data Points

- **SKU registry record count**: 2.1M records
- **SKU lookup P95 latency**: 85ms (target: <20ms)
- **Downstream service dependencies**: 8 services
- **Bundle SKUs in workaround format**: ~12,000
- **Markets requiring locale-specific aliases in Q3**: 4 (EU, APAC, LATAM, CA)

## Preliminary Scorecard Hooks

- Current Architecture Fitness: 2/5 - Does not natively support variants, bundles, or international requirements
- Query Performance: 2/5 - P95 latency 4x over target; index redesign required
- Migration Risk: 3/5 - Phased dual-write approach mitigates but adds complexity
- Standards Readiness: 3/5 - Naming convention standard update is a prerequisite
- Stakeholder Alignment: 4/5 - All teams aligned on need; Q3 timeline is the main risk

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Downstream service breakage during schema migration | High | Medium | Principal Engineer | Phased dual-write with feature flag per service; old schema maintained until all services cut over | 2024-07-01 |
| Naming convention standard gap for multi-market variants | Medium | High | Tech Lead | Update SKU Naming Convention Standard before implementation begins | 2024-05-01 |
| Q3 global expansion timeline conflict | High | Medium | Product Manager | Scope minimal multi-market support for Q3; complete full redesign in Q4 | 2024-06-01 |
| SKU lookup latency remains high during dual-write phase | Medium | Medium | Platform Engineer | Add indexes on new variant hierarchy fields from migration day one | 2024-06-15 |

## Decisions & Next Steps

### Decisions

- New SKU data model will use a three-tier hierarchy: base product, SKU variant, regional configuration
- Migration will use dual-write with per-service feature flags for incremental cutover
- SKU Naming Convention Standard update is a hard prerequisite; no implementation begins until it is approved

### Action Items

- Draft three-tier SKU data model TDD (Principal Engineer - 2024-04-23)
- Update SKU Naming Convention Standard for multi-market variants (Tech Lead - 2024-05-01)
- Map all 8 downstream service dependencies and propose migration order (Platform Engineer - 2024-04-16)
- Scope minimal Q3 multi-market SKU support (Product Manager - 2024-04-16)

### Follow-ups

- TDD review meeting: 2024-04-25
- Weekly project sync every Wednesday starting 2024-04-10
- Brief downstream service teams before 2024-04-23
