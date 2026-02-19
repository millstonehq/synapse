---
id: GUIDE-046
type: guide
title: Building Grafana Dashboards Guide
status: accepted
owner: Engineering Team
created: '2024-02-29T09:43:41.046Z'
updated: '2026-01-07T11:07:20.713Z'
tags:
  - guide
  - monitoring-stack
summary: Building Grafana Dashboards Guide
audience: customer
related_systems:
  - SYSTEM-038
  - SYSTEM-040
related_sops:
  - SOP-079
  - SOP-074
example: true
---

## Why Dashboard Quality Matters

A poorly designed dashboard looks like it has data but fails you in an incident. Panels without units look like they have values but can't be interpreted quickly. Missing threshold lines mean you can't tell at a glance whether a value is good or bad. Dashboards that weren't tested in production show "No data" at the worst moment.

Good dashboards are designed around the questions on-call engineers ask during incidents, not around what data happens to be available. This guide helps you build dashboards that are actually useful.

## The Four Golden Signals First

Every service dashboard should start with four panels that map to the four golden signals: request rate, error rate, latency, and saturation. These four panels answer "is this service healthy" in under 10 seconds. Put them at the top of every service overview dashboard.

Use the standard Grafana dashboard template as your starting point (available in the monitoring config repository). It includes all four golden signal panels pre-configured for the common metric naming convention.

## Designing Panels that Work in Incidents

**Always set units.** A number like "42" on a panel is meaningless. "42 req/s" or "42 ms" is actionable. Grafana supports rich unit formatting — use it. Set units in the Panel Options sidebar.

**Always set threshold lines.** Add a red threshold line at your SLO's critical level and a yellow line at the warning level. On-call engineers can see immediately whether a value is normal, warning, or critical without needing to look up the SLO targets.

**Use the right visualization.** Time series graphs for rates and latencies. Stat panels for current values (error budget remaining, current request rate). Heatmaps for latency distributions. Table panels for per-endpoint breakdowns.

**Avoid panel queries that return thousands of series.** If a query returns more than 20-30 time series, it becomes unreadable. Add `sum by` or `topk` aggregations to keep the panel focused.

## Storing Dashboards in Version Control

All production dashboards must be stored as JSON files in the monitoring configuration repository. Never rely on dashboards saved only in the Grafana UI — they will be lost when the Grafana pod is restarted or the namespace is recreated.

Use the dashboard export button in Grafana to download the JSON. Strip out the `id` field (it's environment-specific) but keep the `uid` field. Commit the JSON to `dashboards/{team}/{service}-{type}.json`.

The Platform team's GitOps pipeline deploys dashboard JSON to Grafana automatically on merge. See the Create New Grafana Dashboard SOP for the full workflow.

## Dashboard Review Checklist

Before submitting a dashboard for production:

- All four golden signals are present if this is a service overview dashboard
- Every panel has a unit set
- Every panel has threshold lines at warning and critical levels
- Dashboard has environment and cluster variable selectors
- Dashboard JSON is committed to the monitoring repository
- A second engineer has reviewed the panel queries for correctness

## Next Steps

- Follow the Create New Grafana Dashboard SOP for the step-by-step creation workflow
- Review the Dashboard Design Standard for the mandatory structure requirements
- Check the Alert Definition Standard to ensure your dashboard thresholds match your alert thresholds
