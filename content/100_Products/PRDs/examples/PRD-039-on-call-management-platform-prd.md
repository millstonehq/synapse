---
id: PRD-039
type: prd
title: On-Call Management Platform PRD
status: accepted
owner: Product Manager
created: '2024-10-19T21:40:30.112Z'
updated: '2025-01-16T00:44:07.508Z'
tags:
  - prd
  - monitoring-stack
summary: On-Call Management Platform PRD
related_tdds:
  - TDD-040
  - TDD-039
example: true
related_standards:
  - STANDARD-045
---

## Summary

Build a unified on-call management platform that replaces the current combination of manual Google Sheets scheduling, PagerDuty direct configuration, and ad-hoc Slack coordination. The platform provides self-service schedule management, fair rotation generation, on-call load visibility, and direct PagerDuty integration. This addresses the problems documented in REPORT-064 (uneven load distribution, on-call burnout score of 2.9/5).

## Goals

- Reduce on-call scheduling toil for team leads by 80% (from ~2 hours/week to < 25 minutes/week)
- Improve on-call load fairness — reduce variance in pages-per-engineer by at least 50%
- Increase on-call satisfaction score from 2.9/5 to at least 3.5/5 within 2 quarters of launch

## In Scope

- Self-service rotation schedule creation with fairness constraints (min gap, max consecutive shifts, timezone grouping)
- PagerDuty schedule synchronization (platform generates schedule; PagerDuty delivers pages)
- On-call load dashboard: pages received, P1 pages, MTTA per engineer per shift
- Shift override and coverage request workflow
- Integration with [[TDD-040|On-Call Scheduling Service]] as the backend
- On-call load distribution report automation (replaces REPORT-064 manual process)

## Out of Scope

- Replacing PagerDuty for alert delivery (PagerDuty remains the notification layer)
- Cross-team on-call coordination (each team manages their own rotation)
- Incident management (separate tooling)
- Compensation tracking for on-call load (HR system concern)

## Users and Flows

**Team leads** are the primary administrators. They define the team's engineer roster and constraints, trigger schedule generation for the next 4 weeks, and approve or modify the generated schedule before it's pushed to PagerDuty. Weekly time commitment: < 25 minutes.

**Engineers** use the platform to view their upcoming on-call shifts, request overrides (swap shifts or find cover), and review their historical on-call load metrics. They also receive weekly shift reminders via Slack integration.

**Engineering managers** use the on-call load dashboard to compare load distribution across teams and identify engineers at risk of burnout before it impacts retention.

## Requirements

- Generate 4-week rotation schedules respecting configurable constraints (minimum 12-hour gap between shifts, max 2 consecutive weekend shifts per engineer per month)
- Publish generated schedules to PagerDuty via API within 60 seconds of generation
- Provide per-engineer shift load metrics: pages received, P1/P2 pages, mean time to acknowledge, total active hours
- Support shift override requests: engineer A requests engineer B covers their shift; B accepts/declines via notification; accepted overrides auto-sync to PagerDuty
- Auto-generate on-call load distribution report monthly (replacing REPORT-064 manual process)
- Integrate dashboard builder ([[TDD-039|TDD-039]]) for on-call load visualization

## KPIs

- **Scheduling time**: Team lead scheduling time < 25 minutes/week (tracked via time-to-approve metric)
- **Load variance**: Standard deviation of pages-per-engineer per shift < 3 (from current ~9)
- **On-call satisfaction**: Bi-annual survey score >= 3.5/5 (from current 2.9/5, measured per [[STANDARD-045|STANDARD-045]])
- **Override SLA**: 95% of override requests resolved (accepted or rejected) within 4 hours

## Information Architecture

- On-Call Management Platform frontend and PRD: `100_Products/`
- Scheduling backend: `90_Architecture/TDDs/TDD-040` (On-Call Scheduling Service)
- Dashboard integration: `90_Architecture/TDDs/TDD-039` (Custom Dashboard Builder)

## Data Model

- **Team**: id, name, pagerduty_schedule_id, constraints (min_gap_hours, max_consecutive_weekends)
- **Engineer**: id, team_id, name, timezone, pagerduty_user_id, unavailability_windows[]
- **Shift**: id, team_id, engineer_id, start_time, end_time, type (primary/secondary)
- **Override**: id, shift_id, requesting_engineer, covering_engineer, status, reason

## Non-Functional

- Schedule generation must complete within 30 seconds for a 10-engineer team with 4-week horizon
- PagerDuty sync must complete within 60 seconds of schedule approval
- Load dashboard must display real-time data with < 5 minute lag
- Platform must be available 99.9% uptime (it is used for critical on-call coordination)

## Constraints

- Must sync with existing PagerDuty account — no PagerDuty account migration
- Schedule generation must respect existing team-defined constraints without requiring re-configuration
- Budget: 2 engineers for 8 weeks

## Risks

- **PagerDuty API deprecation** of schedule sync endpoints. Mitigation: monitor PagerDuty API changelog; platform abstracts PagerDuty via an adapter that can be replaced.
- **Adoption resistance** from teams satisfied with manual scheduling. Mitigation: start with 2 pilot teams; publish load distribution improvements to build internal case.

## Milestones

### M1: Schedule Generation and PagerDuty Sync (Weeks 1-4)
#### Deliverables
- Rotation schedule generator with fairness constraints
- PagerDuty schedule synchronization
- Engineer roster and constraint management UI

#### Acceptance Criteria
- Generated schedule for a 6-engineer team respects all constraints
- Schedule publishes to PagerDuty within 60 seconds of approval

### M2: Load Visibility and Override Workflow (Weeks 5-8)
#### Deliverables
- Per-engineer on-call load dashboard
- Shift override request and approval workflow
- Automated monthly load distribution report

#### Acceptance Criteria
- Load dashboard shows pages-per-engineer data with < 5 minute lag
- Override accepted by covering engineer auto-syncs to PagerDuty within 60 seconds
