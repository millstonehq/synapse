---
id: PROCESS-045
type: process
title: SLO Review and Update Process
status: approved
owner: Engineering Manager
created: '2025-06-24T03:55:58.829Z'
updated: '2025-10-12T05:44:40.231Z'
tags:
  - process
  - monitoring-stack
summary: SLO Review and Update Process
related_standards:
  - STANDARD-048
  - STANDARD-046
related_sops:
  - SOP-076
  - SOP-075
related_systems:
  - SYSTEM-039
example: true
---

## Purpose

This process ensures that Service Level Objectives (SLOs) remain accurate, meaningful, and aligned with both customer expectations and current system capabilities. SLOs must be reviewed regularly because service behavior, traffic patterns, and customer requirements change over time.

A quarterly SLO review cycle gives teams a structured opportunity to assess SLO compliance, adjust targets based on evidence, and update error budget policies to reflect the team's reliability priorities.

## Scope

- All production SLOs registered in the SLO tracking system
- SLI queries backing each SLO in Prometheus
- Error budget policies and burn rate alert thresholds
- SLO compliance reports published to engineering leadership

## Roles and Responsibilities

- **Service Owner**: Prepares the SLO compliance report and proposes any target changes for the review meeting
- **Engineering Manager**: Facilitates the quarterly review meeting and approves SLO target changes
- **Platform Engineer**: Validates SLI query correctness and implements approved changes to recording rules
- **Product Manager**: Provides customer perspective on acceptable service quality; consulted for SLO target changes affecting user-facing services

## Triggers

- Quarterly scheduled SLO review (last week of each quarter)
- SLO breach event — any quarter where the error budget was exhausted triggers an unscheduled review within 2 weeks
- New major feature launch that changes the service's traffic profile or customer expectations
- Service migration or architecture change that affects the SLI measurement methodology

## Inputs

- SLO compliance report for the prior quarter (percentage of time within budget, burn events)
- Incident post-mortems from the prior quarter that cite SLO impacts
- Customer feedback or support tickets related to service reliability
- Current SLO definitions in the SLO tracking system

## Outputs

- Updated SLO definitions with revised targets or adjusted SLI queries if approved
- Quarterly SLO compliance summary shared with engineering leadership
- Updated error budget burn rate alert thresholds if targets change
- Action plan for any SLO that was breached in the prior quarter

## Steps

1. Service Owner pulls the quarterly SLO compliance report from the monitoring platform, documenting error budget consumption per service
2. Service Owner reviews all incident post-mortems from the quarter to identify SLO-related root causes
3. Service Owner prepares the SLO review document summarizing: current target, actual performance, error budget remaining, and recommended changes
4. Engineering Manager schedules the quarterly SLO review meeting with Service Owner, Platform Engineer, and Product Manager
5. Team reviews proposed target changes; changes are accepted if backed by 3+ months of production data and customer impact evidence
6. Platform Engineer validates any revised SLI queries in staging against [[STANDARD-048|SLI/SLO Definition Standard]] and [[STANDARD-046|Alert Definition Standard]]
7. Platform Engineer implements approved SLO and alert changes in a pull request, following the [[SOP-076|Update AlertManager Routes SOP]] for alert changes
8. Engineering Manager publishes the quarterly SLO compliance summary to engineering leadership and updates the SLO changelog

## Controls

- SLO target changes require Engineering Manager approval and must be backed by production performance data
- SLI query changes must be peer-reviewed by the Platform Engineer before deployment
- All SLO changes are logged in the SLO changelog with rationale and approval record
- Services with exhausted error budgets must have a remediation plan before the next release of new features
