---
id: MEETING-036
type: meeting
title: Notification Template System Redesign
status: approved
owner: Product Manager
created: '2024-03-05T05:26:55.531Z'
updated: '2025-06-28T00:13:58.656Z'
tags:
  - meeting
  - notification-service
summary: Notification Template System Redesign
company: NotificationService
topic: Notification Template System Redesign
meeting_date: '2026-11-08T17:06:28.904Z'
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

- **Project**: Notification Service - Template System Redesign
- **Topic**: Notification Template System Redesign
- **Date/Time**: 2026-11-08 17:06 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: The current template system stores templates as flat files in the code repository, requiring a full deployment for any template change. Product wants self-service template editing and the engineering team wants decoupled versioning.

## Observations by Domain

- **Current System Pain Points**: Every template change requires a PR, CI run, and production deployment — average 2-day turnaround; blocking for urgent copy corrections
- **Template Versioning**: The current system has no formal versioning; rollback of a template change requires a full service rollback
- **Localization Gap**: The current system has no i18n support; adding translations requires duplicating template files with no inheritance model
- **Variable Schema Validation**: Variable binding is validated at render time (runtime errors), not at template submission time; this causes silent failures in production
- **Self-Service Demand**: Product and marketing teams want a web UI to edit templates without engineering involvement for routine copy changes

## Key Metrics & Data Points

- **Average template change cycle time**: 2.3 days (PR to production)
- **Template-related production incidents in past year**: 4 (all caused by variable binding errors caught late)
- **Active template count**: 47 across all channels
- **Localization requirement**: 8 languages needed for Q1 expansion
- **Estimated self-service use cases**: 70% of template changes are copy-only with no variable changes

## Preliminary Scorecard Hooks

- Change Velocity: 2/5 - 2-day cycle time unacceptable for urgent copy corrections
- Template Versioning: 1/5 - No versioning, rollback requires service rollback
- Localization Support: 1/5 - No i18n architecture, expansion blocked
- Schema Validation: 2/5 - Runtime only, no compile-time validation
- Self-Service Readiness: 1/5 - No UI, all changes require engineering

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Self-service editing introduces unreviewed templates to production | High | Medium | Principal Engineer | Require approval workflow even for self-service edits | 2026-12-15 |
| Redesign scope creep delays delivery | Medium | High | Tech Lead | Phase implementation: registry first, UI in Phase 2 | 2026-12-01 |

## Decisions & Next Steps

### Decisions

- The template registry will be moved from flat files to a database-backed versioned store
- Phase 1: registry + API + CLI tool (no UI) — targets 30-minute deployment cycle
- Phase 2: web-based editor with approval workflow — enables self-service in Q1

### Action Items

- Principal Engineer to write TDD for template registry redesign (due 2026-11-22)
- Tech Lead to prototype database schema for template versioning (due 2026-11-15)
- Product Manager to gather localization requirements from expansion team (due 2026-11-15)

### Follow-ups

- TDD review before engineering kickoff
- Phase 1 demo to stakeholders upon completion
