---
id: PROCESS-043
type: process
title: New Service Observability Onboarding Process
status: approved
owner: Platform Lead
created: '2024-11-22T13:13:18.999Z'
updated: '2025-02-28T03:29:06.470Z'
tags:
  - process
  - monitoring-stack
summary: New Service Observability Onboarding Process
related_standards:
  - STANDARD-046
  - STANDARD-048
related_sops:
  - SOP-075
  - SOP-073
related_systems:
  - SYSTEM-038
example: true
---

## Purpose

This process ensures that every new production service is properly instrumented and integrated into the monitoring stack before it receives production traffic. Incomplete observability at launch is a leading cause of prolonged incidents, because on-call engineers lack the signals needed to diagnose problems quickly.

By completing this onboarding process, teams confirm that their service emits metrics, logs, and traces in conformance with the applicable standards, and that dashboards, alerts, and runbooks are in place before go-live.

## Scope

- All net-new services being promoted to production for the first time
- Existing services undergoing significant architectural changes (new tech stack, new external dependencies)
- Services migrating from unmanaged or legacy monitoring to the standard monitoring stack

## Roles and Responsibilities

- **Service Owner**: Responsible for instrumenting the service, creating the initial dashboard, and authoring the runbook
- **Platform Engineer**: Reviews metric naming, alert definitions, and trace configuration for compliance with standards; provides the Grafana folder and Prometheus scrape config
- **Engineering Manager**: Approves the production readiness checklist before the service is promoted
- **On-Call Lead**: Confirms that the new service's alerts are integrated into the team's PagerDuty schedule

## Triggers

- A pull request is opened to add a new service to the production manifest
- A service is flagged for observability uplift in the production readiness review
- An engineering team requests onboarding after migrating to a new monitoring platform

## Inputs

- Service name, team ownership, and runtime environment details
- Initial list of proposed metrics, alert names, and SLIs from the service owner
- Access to the Grafana organization and Prometheus configuration repository

## Outputs

- Approved Prometheus scrape configuration for the new service
- Published Grafana dashboard in the team's Grafana folder
- AlertManager rules for all P1/P2 conditions with linked runbooks
- New service entry in the SLO tracking system with defined error budget
- Signed-off production readiness observability checklist

## Steps

1. Service Owner submits the observability onboarding request form, providing service name, team, runtime, and proposed SLIs
2. Platform Engineer creates a Prometheus scrape job entry and verifies the `/metrics` endpoint is reachable in staging
3. Service Owner creates a Grafana dashboard using the standard template, covering the four golden signals (latency, traffic, errors, saturation)
4. Platform Engineer reviews dashboard panels and metric names against [[STANDARD-046|Alert Definition Standard]] and [[STANDARD-048|SLI/SLO Definition Standard]]; provides feedback within 2 business days
5. Service Owner defines alert rules for all critical conditions and links each alert to a runbook per [[SOP-075|Create New Grafana Dashboard SOP]]
6. Service Owner submits the initial SLO definition for review; Platform Engineer validates the SLI query and error budget configuration
7. On-Call Lead adds the new service alerts to the team's PagerDuty routing rules and notifies the on-call rotation
8. Engineering Manager signs off on the production readiness observability checklist; service is approved for production promotion

## Controls

- No service may be promoted to production without a signed observability readiness checklist
- Alert rules must pass automated linting (promtool check rules) in CI before merge
- SLO definitions must be reviewed by a second engineer before being activated in the SLO tracking system
- Onboarding completion is tracked in the platform team's service registry
