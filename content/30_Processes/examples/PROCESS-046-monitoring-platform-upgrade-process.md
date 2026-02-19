---
id: PROCESS-046
type: process
title: Monitoring Platform Upgrade Process
status: approved
owner: Platform Lead
created: '2025-03-03T16:16:30.176Z'
updated: '2026-10-05T09:24:11.511Z'
tags:
  - process
  - monitoring-stack
summary: Monitoring Platform Upgrade Process
related_standards:
  - STANDARD-044
  - STANDARD-047
related_sops:
  - SOP-074
  - SOP-076
related_systems:
  - SYSTEM-039
example: true
---

## Purpose

This process governs the planning, execution, and validation of upgrades to monitoring platform components including Prometheus, Grafana, AlertManager, Jaeger, and the log ingestion pipeline. Monitoring platform upgrades carry elevated risk because a failed upgrade can blind the engineering team to production incidents during and after the upgrade window.

This process ensures that upgrades are carefully planned, tested in staging, and executed with a clear rollback path so that monitoring coverage is maintained throughout.

## Scope

- Major and minor version upgrades to Prometheus, Grafana, AlertManager, Jaeger, and Loki
- Changes to the monitoring platform's Kubernetes manifests, Helm charts, or Terraform configuration
- Storage backend migrations (e.g., moving Prometheus TSDB to Thanos)
- Changes to log ingestion pipeline components (Fluentd/Vector/Logstash configuration)

## Roles and Responsibilities

- **Platform Lead**: Owns the upgrade plan, coordinates the maintenance window, and makes the go/no-go decision
- **Platform Engineer**: Executes the upgrade steps, implements the Prometheus storage scaling via [[SOP-074|Scale Prometheus Storage SOP]] if needed, and performs post-upgrade validation
- **On-Call Lead**: Ensures on-call engineers are briefed before the maintenance window and monitors for alert gaps during upgrade
- **Engineering Manager**: Approves major version upgrades and any changes that affect SLO data continuity

## Triggers

- A monitoring platform component reaches end-of-support within 90 days
- A critical security vulnerability is published for a monitoring platform component
- Scheduled quarterly platform maintenance cycle
- Capacity constraints require a storage or compute upgrade

## Inputs

- Current platform component versions and their changelog/release notes
- Staging environment mirror of the production monitoring stack
- Upgrade plan document with pre-upgrade checklist, execution steps, and rollback procedure
- Change ticket approved by Engineering Manager for major upgrades

## Outputs

- Upgraded monitoring platform components running in production
- Completed upgrade validation report confirming no data loss and no alert regression
- Updated platform runbooks and dashboards reflecting new component versions
- Post-upgrade incident report (only if issues were encountered)

## Steps

1. Platform Lead identifies the target upgrade versions and reviews the relevant changelogs for breaking changes or migration requirements
2. Platform Lead prepares the upgrade plan document, including pre-upgrade backup steps, execution sequence, validation criteria, and rollback procedure per [[STANDARD-044|Structured Logging Standard]] compatibility notes
3. Platform Engineer applies the upgrade to the staging monitoring environment and runs the full validation checklist for at least 48 hours
4. Platform Lead reviews the staging validation results; if any regressions are found, the upgrade is paused until resolved
5. Platform Lead schedules the production maintenance window, notifies engineering teams, and ensures the on-call engineer is briefed
6. Platform Engineer executes the pre-upgrade steps: snapshot storage, validate backup, confirm rollback artifacts are ready
7. Platform Engineer executes the upgrade in production, following the upgrade plan step by step; updates are communicated to #monitoring-ops channel at each major step
8. Platform Engineer runs the post-upgrade validation checklist, verifying metrics ingestion, log ingestion, trace collection, alert firing, and dashboard rendering against [[STANDARD-047|Dashboard Design Standard]]

## Controls

- No major version upgrade without a 48-hour staging validation period
- All upgrades must have a documented and tested rollback procedure
- Upgrades affecting Prometheus TSDB must include a storage backup per [[SOP-074|Scale Prometheus Storage SOP]]
- The on-call rotation must not be changed during an active platform upgrade
