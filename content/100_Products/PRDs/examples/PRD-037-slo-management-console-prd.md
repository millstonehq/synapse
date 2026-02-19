---
id: PRD-037
type: prd
title: SLO Management Console PRD
status: deprecated
owner: Head of Product
created: '2025-11-29T20:14:23.907Z'
updated: '2025-05-11T16:04:28.999Z'
tags:
  - prd
  - monitoring-stack
summary: SLO Management Console PRD
related_tdds:
  - TDD-036
  - TDD-039
example: true
related_standards:
  - STANDARD-048
---

## Summary

Build a self-service SLO Management Console that allows service teams to define, monitor, and manage Service Level Objectives without requiring Monitoring Engineering involvement. Currently SLOs are defined in a spreadsheet and tracked manually — this console automates SLO definition, real-time compliance display, error budget tracking, and automated reporting.

## Goals

- Enable any service team to define and manage their own SLOs without Monitoring Engineering intervention
- Provide real-time error budget visibility so teams can make informed decisions about feature velocity vs. reliability investment
- Automate quarterly SLO compliance reporting currently done manually in spreadsheets

## In Scope

- SLO definition UI (target, indicator metric, window, owner team)
- Real-time error budget remaining and burn rate dashboard
- Historical SLO compliance view (30-day, 90-day)
- Automated burn rate alert configuration from SLO definitions
- Quarterly compliance report generation (PDF export)
- Integration with [[TDD-036|SLO Tracking Service]] as the backend computation layer

## Out of Scope

- SLO recommendations (ML-based target suggestions are v2)
- Customer-facing SLO publishing (separate status page feature)
- SLO approval workflow (team owns their SLOs without a review gate)
- Integration with external SLO platforms (Nobl9, Datadog SLOs)

## Users and Flows

**Service engineers** are the primary users. They access the console to define SLOs for their service during initial setup, monitor error budget consumption daily during operational reviews, and review quarterly compliance when preparing stakeholder reports. They interact via a web UI backed by the SLO Tracking Service REST API.

**Engineering managers** use the console to review cross-team SLO compliance at a glance and to identify services at risk before quarterly planning. They do not define SLOs but need read access to all services.

**On-call engineers** use the error budget burn rate panels during incidents to assess SLO impact and determine whether to escalate based on remaining budget.

## Requirements

- Create, edit, and delete SLO definitions with PromQL-based SLI expressions
- Display real-time error budget remaining as a percentage of the monthly allowance
- Display 1-hour, 6-hour, and 24-hour burn rates with visual indicators (healthy/at-risk/burning)
- Show 28-day rolling compliance chart per SLO
- Auto-generate AlertManager alert rules from SLO definitions (fast burn + slow burn per [[STANDARD-048|STANDARD-048]])
- Export quarterly compliance report as PDF
- Role-based access: team members can edit their own SLOs; managers can read all

## KPIs

- **SLO coverage**: 100% of services with on-call rotations have at least one SLO defined within 90 days of launch
- **Manual reporting eliminated**: Zero engineer-hours spent on manual quarterly SLO compliance reports
- **Burn rate alert adoption**: 80% of SLOs have auto-generated burn rate alerts enabled within 60 days

## Information Architecture

- Console frontend: `100_Products/` (this PRD)
- Backend computation: `90_Architecture/TDDs/` (TDD-036 SLO Tracking Service)
- Dashboard builder integration: `90_Architecture/TDDs/` (TDD-039)
- Alert rule standard: referenced via STANDARD-048

## Data Model

- **SLO**: service, name, target_pct, indicator_metric (PromQL), window_days, owner_team
- **SLOEvaluation**: slo_id, timestamp, remaining_budget_pct, burn_rate_1h, burn_rate_6h, status
- **SLOBreach**: slo_id, breach_start, breach_end, budget_consumed_pct

## Non-Functional

- Console must load within 2 seconds for a team with 10 SLOs
- Real-time data must refresh every 30 seconds without page reload
- SLO Tracking Service must handle 500 SLOs across all teams with < 5s evaluation lag
- All SLO definitions are versioned and auditable (who changed what, when)

## Constraints

- Must use the SLO Tracking Service (TDD-036) as the computation backend — no separate computation layer
- Alert rule generation must produce AlertManager-compatible YAML consumable by the existing provisioning pipeline
- Authentication via existing SSO (no new auth system)

## Risks

- **Poorly defined SLOs** produce misleading burn rate data. Mitigation: provide SLO definition templates with worked examples and a validation tool that shows historical compliance against proposed targets.
- **SLO sprawl** if teams create many low-quality SLOs. Mitigation: limit to 5 SLOs per service at launch; increase limit based on quality signal.

## Milestones

### M1: Core SLO Management (Weeks 1-4)
#### Deliverables
- SLO definition CRUD UI backed by SLO Tracking Service API
- Real-time error budget display and 28-day compliance chart
- Role-based access control

#### Acceptance Criteria
- Engineer can create a SLO with a PromQL expression and see live budget data within 2 minutes
- Manager can view all services' SLO compliance on a single dashboard

### M2: Alert Integration and Reporting (Weeks 5-7)
#### Deliverables
- Auto-generated burn rate alert rules from SLO definitions
- Quarterly compliance PDF report export
- SLO definition templates for common service types

#### Acceptance Criteria
- Creating a SLO automatically generates both fast-burn and slow-burn AlertManager rules
- PDF export contains all SLOs with compliance history for the quarter
