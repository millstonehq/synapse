---
id: PRD-034
type: prd
title: CI/CD Governance Console PRD
status: approved
owner: Senior PM
created: '2024-07-02T07:46:42.984Z'
updated: '2025-09-24T05:03:31.184Z'
tags:
  - prd
  - ci-cd-platform
summary: CI/CD Governance Console PRD
related_tdds:
  - TDD-035
  - TDD-032
example: true
related_standards:
  - STANDARD-038
---

## Summary

Provide engineering leadership and the security team with a CI/CD governance console that gives a unified view of compliance posture across all production services — specifically, which services have required pipeline gates enabled (secret scanning, vulnerability scan, approval workflow, deployment window enforcement) and which are non-compliant. Currently, governance compliance is audited manually on a quarterly basis, which is too slow to catch regressions. The console replaces the quarterly audit spreadsheet with a live, continuously-updated compliance dashboard.

## Goals

- Replace the quarterly manual CI/CD compliance audit with a continuous, automated compliance view
- Give engineering managers a single page showing their team's services and compliance status
- Surface non-compliant services to the platform team within 1 day of a gate being disabled or bypassed
- Provide an audit export for the annual SOC 2 compliance review

## In Scope

- Per-service compliance status for each required gate (secret scanning, vulnerability scan, approval gate, deployment window)
- Fleet-wide compliance percentage and trend over time
- Per-team compliance breakdown for engineering managers
- Non-compliant service alerts delivered to engineering manager via Slack and email
- Compliance history showing when each gate was enabled/disabled and by whom
- CSV and PDF export for audit purposes

## Out of Scope

- Enforcement (the console reports compliance status; enforcement is handled in CI/CD pipelines)
- DORA metrics (covered by dedicated reporting tools)
- Security vulnerability detail (Trivy dashboard covers this separately)
- Compliance with non-CI/CD standards (security policies, data handling, etc.)

## Users and Flows

**Engineering managers** use the governance console during weekly team reviews to see whether any of their services have become non-compliant since the last review. A non-compliant service triggers a Slack notification; the manager clicks through to the console to see which gate is missing, who disabled it, and links to the PR that changed the configuration. They assign a ticket to the service owner to remediate.

**Platform team engineers** use the fleet-wide view to identify systemic non-compliance patterns (e.g., 20% of services lack the new canary gate because the onboarding template hasn't been updated). They use this data to prioritize platform work and measure adoption of newly launched gates.

**Security and compliance team** uses the audit export feature to pull a point-in-time compliance snapshot for the SOC 2 auditor, replacing the manual spreadsheet they currently maintain.

## Requirements

- Collect gate configuration data from GitHub Actions workflow files and CI/CD platform configuration for all registered services
- Evaluate each service against a configurable required gate list (updated by the platform team as new gates are introduced)
- Display per-service compliance status as a green/yellow/red indicator per gate
- Send a Slack notification to the service owner's team channel when a service transitions from compliant to non-compliant
- Track compliance history with the identity of the engineer who changed the gate configuration
- Provide a CSV export of compliance status for all services at a given point in time
- Refresh compliance status within 1 hour of a CI configuration change being pushed to a service repository

## KPIs

- **Fleet compliance rate**: Target > 95% of services compliant with all required gates
- **Compliance detection lag**: Non-compliance detected within 1 hour of a gate being removed
- **Audit preparation time**: SOC 2 compliance export generated in < 5 minutes vs. current 2-day manual process
- **Manager engagement**: > 70% of engineering managers logging into the console at least once per week within 60 days of launch

## Information Architecture

- Technical design in `90_Architecture/TDDs/` (see [[TDD-035|TDD-035]] and [[TDD-032|TDD-032]])
- Governance standards defining required gates live in `20_Standards/`
- This PRD in `100_Products/PRDs/`

## Data Model

- **ServiceComplianceRecord**: `service_name`, `team`, `evaluated_at`, `required_gates` (JSON), `status_per_gate` (JSON map), `overall_compliant`
- **ComplianceEvent**: Immutable log of gate status changes: `service_name`, `gate_name`, `from_status`, `to_status`, `changed_by`, `pr_url`, `occurred_at`
- **RequiredGateConfig**: `gate_name`, `description`, `effective_date`, `enforcement_level` (required/recommended) — managed by platform team

## Non-Functional

- Compliance data refreshed within 1 hour of a CI configuration push
- Audit export generated within 30 seconds for up to 500 services
- Console page loads within 2 seconds for a manager's team view (up to 50 services)
- Read-only access for all authenticated users; write access (gate config updates) restricted to platform team

## Constraints

- Must not require service teams to instrument their CI pipelines with compliance reporting agents; compliance is derived by analyzing existing workflow files
- Must use existing SSO for authentication; no additional identity management
- Export format must be CSV and PDF for auditor compatibility

## Risks

- **False compliance signals** if the analyzer misreads a complex workflow file. Mitigation: analyzer produces an "indeterminate" status (yellow) rather than false-compliant when a workflow is too complex to parse; manual review flag is set.
- **Scope creep to enforcement** as managers ask why the console can't block deployments for non-compliant services. Mitigation: enforcement is a separate initiative; document the boundary in the PRD and in the console UI.

## Milestones

### M1: Compliance Analyzer and Data Collection (Weeks 1-3)

#### Deliverables

- Analyzer that reads GitHub Actions workflow files and extracts gate configuration
- ComplianceRecord storage with hourly refresh job
- Initial required gate list configurable by platform team

#### Acceptance Criteria

- Analyzer correctly identifies gate status for 10 pilot services validated against manual review
- Refresh job completes within 30 minutes for 200 services

### M2: Console UI and Notifications (Weeks 4-6)

#### Deliverables

- Per-service compliance view with gate-level status indicators
- Fleet-wide and per-team summary views
- Slack notification on non-compliance transition

#### Acceptance Criteria

- Manager can see all their team's services and compliance status on one page
- Non-compliance Slack notification delivered within 70 minutes of a gate being removed from a workflow file
