---
id: PROCESS-044
type: process
title: Alert Tuning Process
status: approved
owner: Director of Engineering
created: '2024-08-15T04:59:24.292Z'
updated: '2026-08-25T23:50:58.955Z'
tags:
  - process
  - monitoring-stack
summary: Alert Tuning Process
related_standards:
  - STANDARD-043
  - STANDARD-045
related_sops:
  - SOP-077
  - SOP-071
related_systems:
  - SYSTEM-036
example: true
---

## Purpose

This process governs the ongoing review and adjustment of alert thresholds, routing rules, and suppression policies in the monitoring stack. Alert tuning is necessary to reduce alert fatigue, improve signal-to-noise ratio, and ensure that on-call engineers receive actionable notifications rather than noise.

Alert quality degrades over time as services evolve, traffic patterns change, and thresholds that were once appropriate become either too sensitive or too permissive. This process provides a structured cadence for reviewing and improving alerts.

## Scope

- All Prometheus alerting rules in the production AlertManager configuration
- PagerDuty routing rules and escalation policies
- Alert suppression and silencing policies
- Alert documentation and runbook linkage

## Roles and Responsibilities

- **On-Call Engineer**: Logs noisy or low-quality alerts during their rotation as input for the tuning cycle
- **Team Lead**: Facilitates the monthly alert review meeting and prioritizes tuning work
- **Platform Engineer**: Implements approved changes to AlertManager rules and PagerDuty routing
- **Engineering Manager**: Reviews and approves significant threshold changes and escalation policy modifications

## Triggers

- Monthly scheduled alert quality review (first Tuesday of the month)
- Alert noise report showing more than 20% of alerts were acknowledged but resolved without action
- Post-incident review identifies an alert that failed to fire or fired too late
- New service onboarding adds alerts that have not yet been tuned in production

## Inputs

- Alert volume report from the previous 30 days (PagerDuty and AlertManager statistics)
- On-call engineer feedback log from recent rotations
- Post-incident reports identifying alert gaps or noise issues
- Current AlertManager configuration in version control

## Outputs

- Updated AlertManager rules with revised thresholds, for durations, and annotations
- Updated runbook links and alert descriptions
- Closed or archived alerts that no longer correspond to actionable conditions
- Alert quality metrics report shared with engineering leadership

## Steps

1. Platform Engineer generates the monthly alert volume report, showing firing frequency, acknowledge rate, and action rate per alert
2. Team Lead reviews the report and collects on-call feedback from engineers who rotated in the past month
3. Team Lead facilitates the alert review meeting, categorizing each flagged alert as: tune threshold, improve runbook, silence, or archive
4. On-Call Engineers and Platform Engineers collaboratively determine new threshold values using historical data from Prometheus
5. Platform Engineer implements approved changes in a pull request against the AlertManager configuration repository; changes are validated with `promtool check rules`
6. Changes are deployed to staging and monitored for one week; alerts must not regress in staging before production deployment
7. Platform Engineer deploys approved changes to production AlertManager and updates the alert changelog
8. Team Lead confirms that all archived alerts have had runbooks updated or deprecated accordingly

## Controls

- All AlertManager rule changes must pass CI linting and peer review before merge
- Threshold increases (making alerts less sensitive) require Team Lead approval; threshold decreases require Engineering Manager approval
- The alert quality score (action rate / total fires) must be tracked monthly and must remain above 70%
- Changes to P1 alert thresholds require post-change monitoring for 48 hours before being considered stable
