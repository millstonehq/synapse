---
id: SOP-075
type: sop
title: Create New Grafana Dashboard SOP
status: accepted
owner: SRE Lead
created: '2025-02-11T18:34:56.187Z'
updated: '2026-04-30T10:50:37.934Z'
tags:
  - sop
  - monitoring-stack
summary: Create New Grafana Dashboard SOP
related_process: PROCESS-043
related_systems:
  - SYSTEM-039
example: true
---

## Preconditions

- The service emitting the metrics you want to dashboard has been onboarded to the monitoring stack
- You have identified the metric names to be visualized (they follow the naming convention in STANDARD-043)
- You have Grafana Editor access to the team's Grafana folder
- You have reviewed the Dashboard Design Standard (STANDARD-047) requirements

## Materials/Access

- Grafana Editor access for the relevant team folder
- Access to the Grafana dashboard template (stored in the monitoring config repository)
- List of metric names and label sets to be visualized
- Prometheus data source configured and accessible in Grafana
- Git access to the monitoring configuration repository for saving dashboard JSON

## Procedure

1. Open Grafana and navigate to your team's folder. Click "New Dashboard" and then "Import" to load the standard team dashboard template from the monitoring config repository.
2. Set the dashboard title to the pattern `[Service Name] - [View Type]` (e.g., `Auth Service - Overview`) and set the UID to a short, descriptive slug (e.g., `auth-overview`).
3. Add a Variables row at the top of the dashboard with `env` (environment), `cluster`, and time range selectors. Use the standard variable query templates from the template.
4. Create the four golden signals panels in order: Request Rate (`rate({service}_http_requests_total[5m])`), Error Rate (ratio of 5xx to total), P95 Latency (`histogram_quantile(0.95, ...)`), and Saturation (CPU and memory utilization).
5. For each panel, set the unit to match the metric unit (use `req/s`, `%`, `s` as appropriate) and add meaningful axis labels. Set threshold lines at your service's SLO warning and critical levels.
6. Add color thresholds to each panel: green below warning, yellow between warning and critical, red above critical. Use the standard color values from the Dashboard Design Standard.
7. Add a Links panel at the bottom of the dashboard containing links to: the relevant runbook, the AlertManager rules for this service, and the Jaeger trace search URL for this service.
8. Save the dashboard in Grafana to get the JSON. Export the JSON and commit it to the monitoring configuration repository under `dashboards/{team}/{service}-overview.json`.
9. Submit a pull request with the dashboard JSON. The Platform Engineer will review for standards compliance and merge to trigger the GitOps deployment.

## Validation

- The dashboard renders correctly in Grafana with no "No data" panels for the target service in production
- All four golden signals panels display current data and match expected values
- Variables (env, cluster) correctly filter all panels when changed
- Dashboard JSON is committed to the monitoring repository and deployed via GitOps
- A second engineer has reviewed the dashboard against the Dashboard Design Standard

## Rollback

1. If the dashboard causes performance issues in Grafana (very slow load), disable expensive queries by commenting them out in the panel editor.
2. To remove a dashboard from production, delete the JSON file from the monitoring repository and submit a PR. Do not delete manually in the Grafana UI.
3. If the GitOps deployment fails, the previous dashboard version will remain active until the issue is resolved.
