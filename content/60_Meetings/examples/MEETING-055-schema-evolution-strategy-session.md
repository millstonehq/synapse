---
id: MEETING-055
type: meeting
title: Schema Evolution Strategy Session
status: approved
owner: Engineering Manager
created: '2024-10-27T05:36:51.839Z'
updated: '2026-05-02T21:08:39.808Z'
tags:
  - meeting
  - data-pipeline
summary: Schema Evolution Strategy Session
company: DataPipeline
topic: Schema Evolution Strategy Session
meeting_date: '2024-05-06T05:53:10.993Z'
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

- **Project**: Schema Governance Initiative
- **Topic**: Schema Evolution Strategy Session
- **Date/Time**: 2024-05-06 9:00 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Schema Registry Maintainer
- **Attendees (product)**: Engineering Manager, QA Lead
- **Context**: Following two schema-breaking incidents in Q1 that caused consumer outages, this session defines the organization's schema evolution strategy and governance process.

## Observations by Domain

- **Incident Root Causes**: Both Q1 incidents were caused by field removals deployed without consumer notification; no compatibility check was enforced in CI.
- **Current Registry State**: 22 topics registered; compatibility mode is NONE for 8 topics (no compatibility enforcement at all).
- **Schema Ownership**: Schema ownership is not declared for 12 of 22 topics; no clear owner to coordinate changes with consumers.
- **Consumer Inventory**: No automated mechanism to identify which services consume a given topic; relies on tribal knowledge.
- **Deprecation Practice**: No formal deprecation process; fields are removed immediately without a transition period.
- **Tooling**: Schema compatibility checks exist in the CLI but are not integrated into CI for producer services.

## Key Metrics & Data Points

- **Topics with NONE compatibility mode**: 8/22 (36%)
- **Topics with undeclared ownership**: 12/22
- **Schema-breaking incidents Q1**: 2 (both caused consumer outages)
- **Average consumer outage duration from schema incident**: 47 minutes
- **Consumer inventories automated**: 0/22 topics
- **CI compatibility check coverage**: 0 producer services

## Preliminary Scorecard Hooks

- Schema Governance: 2/5 - No compatibility enforcement for 36% of topics; ownership unclear
- Incident Prevention: 1/5 - No CI gate catching breaking changes before production
- Consumer Protection: 2/5 - No consumer inventory; consumers unaware of upcoming changes
- Deprecation Practice: 1/5 - No formal deprecation period; immediate removal pattern
- Registry Health: 3/5 - Registry itself is reliable; governance layer is the gap

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| NONE-mode topics will break consumers on next schema change | High | High | Principal Engineer | Set all topics to BACKWARD_COMPATIBLE compatibility mode | 2024-05-20 |
| No CI gate means breaking changes reach production unchecked | High | High | Tech Lead | Add schema compatibility check to all producer CI pipelines | 2024-06-01 |
| Unknown consumer inventory prevents safe field removal | High | High | Schema Registry Maintainer | Implement consumer tracking in registry metadata | 2024-06-15 |
| No deprecation period exposes consumers to sudden field loss | Medium | Certain | Engineering Manager | Enforce 14-day deprecation notice policy via schema evolution process | 2024-05-15 |

## Decisions & Next Steps

### Decisions

- All Kafka topics must be set to BACKWARD_COMPATIBLE compatibility mode by May 20; NONE mode is prohibited
- A CI-enforced schema compatibility check is mandatory for all producer services before end of May
- A formal 14-day deprecation notice is required before any field removal; enforced by the Schema Evolution Process

### Action Items

- Migrate all 8 NONE-mode topics to BACKWARD_COMPATIBLE (Principal Engineer - 2024-05-20)
- Add schema compatibility check step to all producer CI pipelines (Tech Lead - 2024-06-01)
- Document and publish the schema evolution process (Engineering Manager - 2024-05-15)

### Follow-ups

- Monthly schema health review to track compatibility mode compliance
- Post-implementation review of CI compatibility check effectiveness in 60 days
