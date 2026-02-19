---
id: PRD-036
type: prd
title: Unified Observability Dashboard PRD
status: accepted
owner: Product Manager
created: '2024-06-27T05:35:35.531Z'
updated: '2025-01-12T09:50:19.178Z'
tags:
  - prd
  - monitoring-stack
summary: Unified Observability Dashboard PRD
related_tdds:
  - TDD-039
  - TDD-040
example: true
related_standards:
  - STANDARD-045
---

## Summary

The Unified Observability Dashboard consolidates metrics, logs, traces, and alert state from disparate monitoring tools into a single pane of glass for engineering and operations teams. Today, on-call engineers must context-switch between Grafana, Kibana, Jaeger, and multiple cloud console tabs to diagnose production incidents, adding 10–15 minutes of mean time to diagnosis per page. This product replaces that fragmented workflow with a cohesive, role-tailored dashboard surface built on top of the existing monitoring stack.

The dashboard is not a new data store. It federates queries against Prometheus, Loki, Tempo, and the alerting ruleset already operated by the platform team, surfaces correlated signals, and exposes a shared URL scheme so that runbooks and postmortems can link directly to time-bounded views. See [[TDD-039|Observability Dashboard Technical Design]] for the architectural implementation.

## Goals

- Reduce mean time to diagnosis (MTTD) for P1/P2 incidents by 40% within 90 days of GA launch
- Give every on-call engineer a single starting point that surfaces correlated signals without manual tab-switching
- Enable service owners to build and publish team-specific dashboard panels without requiring platform team involvement
- Replace three manually maintained static dashboards (infra, application, data pipeline) with dynamically rendered views from live data

## In Scope

- Unified home view showing active alerts, top error-rate services, and infrastructure health at a glance
- Correlated trace-to-log drill-down: clicking a slow span surfaces co-located log lines from the same trace ID
- Service catalog integration: each service entry links to its default dashboard view
- Shareable, time-locked URLs that encode the selected time range and panel filters
- Role-based panel visibility: infrastructure panels hidden from product-only stakeholders
- Self-service panel builder allowing teams to define panels via YAML committed to the platform repository
- Alert annotation overlays on metric charts showing when firing alerts occurred

## Out of Scope

- Replacing Grafana or Prometheus as the underlying data layer (we federate, we do not fork)
- Mobile-optimized layout (desktop-first; responsive improvements deferred to v2)
- Custom alerting rule authoring through the dashboard UI (editing rules remains in the platform repo via [[STANDARD-045|Alerting Standards]])
- Real-user monitoring (RUM) or synthetic monitoring (separate initiative)

## Users and Flows

The primary user is the on-call engineer who receives a PagerDuty alert and opens the dashboard as their first action. Within seconds they need to see: which alerts are firing, which services are affected, and whether the issue correlates with a recent deploy. The dashboard surfaces this triage view automatically on load, scoped to the last 30 minutes and filtered to the on-call engineer's team by default. From the triage view they can pivot to a trace waterfall or jump to correlated log lines without leaving the application.

Service owners and tech leads use the dashboard during and after incidents to review SLO burn rates, error budgets, and latency percentile trends. They interact with the panel builder to create team dashboards that are reviewed quarterly. These users spend more time in the historical drill-down view than the live triage view.

Engineering managers and directors access read-only summary views showing weekly SLO status and incident counts by service. This audience uses shareable dashboard URLs embedded in weekly reports and postmortem documents rather than navigating the dashboard interactively.

## Requirements

- Display a live triage view showing all currently firing alerts grouped by service and severity, refreshing every 30 seconds
- Render metric charts for CPU, memory, request rate, error rate, and P95 latency for any selected service over any time range up to 90 days
- Correlate a distributed trace span with log lines sharing the same trace ID and display them side by side in a split panel
- Surface deploy event markers on metric charts by reading deployment annotations from the events API
- Support team-scoped filtering so engineers see only services owned by their team by default, with the ability to expand to all services
- Resolve panel definitions from YAML files in the platform repository and hot-reload changes without a dashboard deployment
- Generate a shareable URL that reproduces the exact time range, selected service, and panel layout when opened by another user
- Enforce role-based access: infrastructure-level panels (node metrics, cloud cost) visible only to platform team members

## KPIs

- **MTTD reduction**: Mean time to diagnosis for P1/P2 incidents decreases by 40% vs. 90-day pre-launch baseline
- **Dashboard adoption**: 90% of on-call engineers open the dashboard as their first action within 60 days of launch, measured via session analytics
- **Self-service panel creation**: Teams publish at least 10 net-new YAML-defined panels in the first quarter post-launch without platform team assistance
- **Page load time**: Dashboard home view renders in under 2 seconds at P95 on a standard corporate laptop
- **Static dashboard retirement**: All three legacy static dashboards decommissioned within 60 days of GA

## Information Architecture

- This PRD lives in `100_Products/PRDs/` and is the requirements source of record
- Technical implementation is documented in [[TDD-039|Observability Dashboard Technical Design]] and [[TDD-040|Panel Builder YAML Schema]] in `90_Architecture/TDDs/`
- Operational runbooks for the dashboard service itself are published to `50_Runbooks/`
- The YAML panel schema reference and contribution guide are published to `80_Guides/` for service teams
- Alert annotation and SLO burn rate data contracts are governed by [[STANDARD-045|Alerting Standards]]

## Data Model

- **DashboardDefinition**: A persisted user-or-team-owned layout consisting of an ordered list of PanelRef IDs, a default time range, and a default service filter
- **PanelRef**: A pointer to a panel resolved at render time; includes the panel type (`metric`, `log`, `trace`, `alert-list`), the data source ID, and query parameters
- **PanelDefinition**: The canonical panel specification stored in YAML; fields include `id`, `title`, `type`, `datasource`, `query`, `owner_team`, and `visibility` (public or team-scoped)
- **ShareableLink**: An encoded URL payload capturing `dashboard_id`, `time_from`, `time_to`, `service_filter`, and `panel_focus`; links expire after 90 days
- **AlertAnnotation**: An event record with `fired_at`, `resolved_at`, `alert_name`, `service`, and `severity`, written by the alertmanager integration and overlaid on metric charts

## Non-Functional

- Dashboard service must achieve 99.9% monthly availability; it is a supporting tool, not in the critical path for payment or order processing
- All data source queries must time out within 5 seconds and degrade gracefully by rendering a partial view rather than a blank page
- Role-based access control must integrate with the existing SSO provider; no separate user store
- Panel YAML definitions are version-controlled in the platform repository and subject to the same code review process as infrastructure changes
- Shareable links must not expose data to unauthenticated users; opening a link without an active session redirects to SSO login

## Constraints

- Must federate from existing Prometheus, Loki, and Tempo instances operated by the platform team; no new observability backends will be provisioned
- Engineering budget is 2 senior engineers for 12 weeks; no additional headcount
- Must ship as a containerized service deployable on the existing Kubernetes cluster; no new cloud services may be introduced
- The self-service panel builder must not allow arbitrary query injection; queries must be parameterized templates selected from an approved list

## Risks

- **Query fan-out latency**: Federated queries across multiple data sources may exceed the 5-second timeout under high cardinality. Mitigation: instrument query latency from day one and work with the platform team to add recording rules for common high-cardinality queries before GA.
- **YAML schema adoption friction**: Service teams may resist learning a new panel format if tooling support is poor. Mitigation: provide a VS Code schema extension and a CI linter that validates panel YAML on pull request, shipping both before the public announcement.
- **SSO dependency at launch**: If the SSO integration is delayed, the dashboard cannot enforce role-based visibility. Mitigation: define a feature flag that disables infrastructure panels entirely until SSO is verified in production.
- **Static dashboard retirement resistance**: Teams with customized legacy dashboards may block decommissioning. Mitigation: commit to a one-for-one migration assistance offer — platform team will convert any legacy dashboard to YAML panels on request.

## Milestones

### M1: Core Dashboard and Data Federation (Weeks 1-5)

#### Deliverables

- Authenticated dashboard application deployed to staging with SSO integration
- Live triage home view showing firing alerts and top-error-rate services
- Metric, log, and trace panels functional for any service in the catalog
- Shareable URL encoding implemented and verified

#### Acceptance Criteria

- On-call engineer can open the home view and identify a firing alert's affected service within 30 seconds
- Clicking a trace span renders correlated log lines from the same trace ID
- A shareable link opened in a private browser session redirects to SSO and then restores the exact panel state
- All data source queries degrade gracefully (partial view, not blank page) when a backend times out

### M2: Self-Service Panel Builder and Role-Based Access (Weeks 6-9)

#### Deliverables

- YAML panel schema finalized and published with VS Code extension and CI linter
- Panel builder resolves YAML definitions from the platform repository at dashboard load time
- Role-based panel visibility enforced via SSO group membership
- Deploy event annotations overlaid on metric charts

#### Acceptance Criteria

- A service team can add a new panel by merging a YAML file to the platform repository and see it appear without a dashboard redeployment
- Infrastructure panels are hidden from users not in the `platform-team` SSO group
- Deploy annotation markers appear on metric charts within 2 minutes of a deployment event being recorded

### M3: GA Launch and Legacy Dashboard Retirement (Weeks 10-12)

#### Deliverables

- Three legacy static dashboards migrated to YAML panel definitions
- Production deployment with load testing validating P95 home view load under 2 seconds
- On-call runbook and user guide published
- Rollout communication sent to all engineering teams

#### Acceptance Criteria

- Legacy static dashboards return 301 redirects to the unified dashboard for all existing bookmark URLs
- P95 home view load time is under 2 seconds under simulated load of 50 concurrent users
- 80% of on-call engineers confirm in a post-launch survey that the dashboard is their first stop during incidents
