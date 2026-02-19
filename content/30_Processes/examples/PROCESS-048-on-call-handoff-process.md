---
id: PROCESS-048
type: process
title: On-Call Handoff Process
status: approved
owner: Platform Lead
created: '2025-10-22T03:34:37.512Z'
updated: '2026-09-06T08:50:02.709Z'
tags:
  - process
  - monitoring-stack
summary: On-Call Handoff Process
related_standards:
  - STANDARD-045
  - STANDARD-047
related_sops:
  - SOP-080
  - SOP-078
related_systems:
  - SYSTEM-040
example: true
---

## Purpose

This process ensures a reliable and consistent handoff of on-call responsibility between outgoing and incoming engineers. A well-executed handoff prevents service continuity gaps, ensures the incoming engineer is fully briefed on active issues, and maintains the integrity of incident tracking records.

Without a formal handoff, incoming on-call engineers can be caught unaware of ongoing incidents, silenced alerts, or infrastructure changes in progress, all of which can delay or worsen incident response.

## Scope

- All scheduled on-call rotation handoffs for production services
- Emergency handoffs when an on-call engineer becomes unavailable mid-shift
- Handoffs following major incidents where additional context is critical for the incoming engineer

## Roles and Responsibilities

- **Outgoing On-Call Engineer**: Prepares the handoff notes, reviews open items, and briefs the incoming engineer
- **Incoming On-Call Engineer**: Reviews handoff notes, confirms understanding of open issues, and takes ownership in PagerDuty
- **Team Lead**: Reviews handoff notes weekly; escalates persistent issues that are not being resolved between shifts
- **Platform Lead**: Maintains the handoff note template and ensures the process is followed; reviews compliance with [[STANDARD-047|Dashboard Design Standard]] for active issue dashboards

## Triggers

- Scheduled end of on-call rotation (weekly, by default)
- Emergency handoff triggered by on-call engineer unavailability (illness, emergency)
- Explicit handoff requested after a significant incident has occurred during the shift

## Inputs

- Outgoing engineer's handoff notes document
- Active PagerDuty incidents and silenced alerts at time of handoff
- List of any recent infrastructure changes or platform upgrades completed during the shift
- Open post-incident action items assigned to the outgoing engineer

## Outputs

- Completed handoff notes reviewed and acknowledged by incoming engineer
- PagerDuty schedule updated to reflect incoming engineer as primary
- Open incidents and action items transferred to incoming engineer in the tracking system
- Any outstanding alerts that need follow-up flagged for the Team Lead

## Steps

1. Outgoing On-Call Engineer drafts the handoff document at least 1 hour before rotation end, including: active incidents, silenced alerts with expiry times, recent changes, and open action items
2. Outgoing engineer highlights any Prometheus cardinality or storage issues per [[SOP-078|Handle Prometheus Cardinality Explosion SOP]] that are being monitored but not yet resolved
3. Outgoing engineer schedules a 15-minute handoff call with the incoming engineer
4. During the call, outgoing engineer walks through each active item; incoming engineer asks clarifying questions and confirms understanding
5. Incoming On-Call Engineer confirms the handoff in PagerDuty by accepting the on-call shift; outgoing engineer verifies they are no longer primary
6. Incoming engineer verifies that all active dashboards are rendering correctly and that their PagerDuty notification settings are configured
7. Outgoing engineer posts handoff notes in the on-call channel and tags the Team Lead for visibility
8. Team Lead reviews the handoff notes within 24 hours and follows up on any items requiring escalation

## Controls

- Handoff calls are mandatory; asynchronous-only handoffs are not permitted for P1 or active incidents
- Silenced alerts must be reviewed at every handoff; any silence expiring during the next shift must be explicitly re-evaluated
- Handoff notes must be stored in the on-call log for at least 90 days
- PagerDuty schedule changes must be confirmed by both outgoing and incoming engineers before the handoff is considered complete
