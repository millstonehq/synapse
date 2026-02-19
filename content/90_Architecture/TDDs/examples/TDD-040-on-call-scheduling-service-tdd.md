---
id: TDD-040
type: tdd
title: On-Call Scheduling Service TDD
status: approved
owner: Senior Engineer
created: '2024-02-06T10:00:52.034Z'
updated: '2025-05-24T15:43:57.322Z'
tags:
  - tdd
  - monitoring-stack
summary: On-Call Scheduling Service TDD
related_adrs:
  - ADR-0033
  - ADR-0032
example: true
---

## Summary

Design an on-call scheduling service that manages engineer rotation schedules, enforces fairness constraints, integrates with PagerDuty for schedule synchronization, and provides an API for the Alert Management Service to resolve the current on-call engineer for any team. This replaces manual spreadsheet-based scheduling and closes the gap identified in REPORT-064 (uneven on-call load distribution).

The service enforces constraints from [[ADR-0033|ADR-0033]] (error budget burn rate alerting) by routing high-urgency alerts to the correct on-call engineer via the Alert Management Service, and logs rotation state to the log aggregation system described in [[ADR-0032|ADR-0032]] for audit and analysis.

## Overview

- **Fair scheduling algorithm**: Generates rotation schedules that distribute shifts equitably, accounting for past on-call load, time zone preferences, and unavailability windows (holidays, PTO).
- **PagerDuty synchronization**: Publishes schedules to PagerDuty via its REST API. PagerDuty remains the source of truth for actual on-call notifications; this service is the source of truth for schedule generation.
- **Load tracking**: Records each shift's actual alert load (pages received, hours spent) to inform future scheduling and the on-call load distribution report.
- **Override management**: Provides an API for engineers to register temporary overrides (swap shifts, request cover) that propagate to PagerDuty automatically.

## Architecture

- **Schedule generator**: Given a team's engineer list, constraints, and look-ahead window (4 weeks), produces an optimized rotation schedule using a constraint-satisfaction algorithm (minimum shift gap, max consecutive shifts, timezone grouping).
- **PagerDuty sync**: Pushes generated schedules to PagerDuty's schedule API. Runs as a nightly job and on-demand after overrides.
- **On-call resolver API**: `GET /api/v1/oncall/{team}` returns the current on-call engineer for a team. Used by the Alert Management Service for routing context.
- **Load recorder**: Consumes alert delivery events from the Alert Management Service to record per-shift page counts and resolution times.
- **Override API**: CRUD API for shift overrides; propagates changes to PagerDuty within 60 seconds.

## Information Model

- **Engineer**: `id`, `name`, `email`, `pagerduty_id`, `timezone`, `team_memberships[]`
- **Shift**: `id`, `team`, `engineer_id`, `start_time`, `end_time`, `override_reason`
- **Schedule**: `team`, `generated_at`, `shifts[]` (4-week window)
- **ShiftLoad**: `shift_id`, `pages_received`, `p1_pages`, `time_to_ack_avg_min`, `hours_active`
- **Constraint**: `team`, `type` (min_gap_hours, max_consecutive, timezone_group), `value`

## Interfaces

- `GET /api/v1/oncall/{team}` — current on-call engineer for a team (used by Alert Management Service)
- `GET /api/v1/schedules/{team}?weeks=4` — upcoming schedule for a team
- `POST /api/v1/overrides` — create a shift override
- `DELETE /api/v1/overrides/{id}` — cancel an override
- `POST /api/v1/schedules/{team}/generate` — trigger schedule generation for a team
- PagerDuty REST API v2 — schedule sync, on-call lookup

## Files and Layout

```
cmd/oncall-scheduler/main.go
internal/
  scheduler/                 - Constraint-satisfaction schedule generator
  pagerduty/                 - PagerDuty API client, schedule sync
  resolver/                  - On-call lookup API handler
  loadrecorder/              - Alert load recording from Alert Management Service events
  overrides/                 - Override management, PagerDuty propagation
  store/                     - PostgreSQL repository (engineers, schedules, loads)
```

## Work Plan

1. **Phase 1 (Week 1-2)**: Data model, PostgreSQL schema, engineer and constraint CRUD APIs
2. **Phase 2 (Week 3)**: Schedule generation algorithm, constraint validation, unit tests for fairness properties
3. **Phase 3 (Week 4)**: PagerDuty sync integration, on-call resolver API
4. **Phase 4 (Week 5)**: Override management, load recorder, integration with Alert Management Service
5. **Phase 5 (Week 6)**: Production deployment with one team pilot; compare generated schedules to manual schedules

## Risks and Mitigations

- **Risk**: Schedule generation produces unfair results for small teams (< 4 engineers). **Mitigation**: Minimum viable rotation requires 4 engineers; service surfaces a warning and requires manual override for smaller teams.
- **Risk**: PagerDuty API rate limits delay schedule sync after overrides. **Mitigation**: Override propagation is async; PagerDuty sync queued and executed within 60 seconds, not immediately.
- **Risk**: On-call resolver API becoming critical path for alert routing. **Mitigation**: Cache on-call state in Redis with 5-minute TTL; resolver returns cached value if the database is unavailable (fail-open with warning).
