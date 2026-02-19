---
id: GUIDE-043
type: guide
title: Getting Started with Observability Stack
status: approved
owner: Engineering Team
created: '2025-04-20T09:45:59.425Z'
updated: '2025-10-17T10:03:57.802Z'
tags:
  - guide
  - monitoring-stack
summary: Getting Started with Observability Stack
audience: partner
related_systems:
  - SYSTEM-039
  - SYSTEM-036
related_sops:
  - SOP-072
  - SOP-071
example: true
---

## Why Observability Matters

Without observability, production systems are black boxes. When something goes wrong at 2am, you need to be able to answer three questions quickly: is the system degraded, which part is degraded, and why. Metrics answer the first question, logs answer the third, and traces answer the second.

Our observability stack is built around three signal types: metrics in Prometheus, structured logs in Loki, and distributed traces in Jaeger. Together they give you the full picture of your service's behavior in production. This guide walks you through accessing each signal and understanding when to use which.

## Prerequisites

Before you start, confirm you have:

- A Grafana account (request via IT if needed — access is provisioned within 24 hours)
- Your service is emitting the three signal types (check with the Platform team if unsure)
- Familiarity with your service's Prometheus metric names (check the service's `README` or the Prometheus scrape config)

## Navigating the Three Signal Types

### Metrics (Prometheus + Grafana)

Start with your service's overview dashboard in Grafana. Every production service should have one. If yours doesn't exist yet, follow the Create New Grafana Dashboard SOP to build it.

The four panels to look at first: request rate (is traffic normal?), error rate (is anything failing?), P95 latency (is it slow?), and saturation (are resources exhausted?). These four golden signals tell you whether your service is healthy in under 10 seconds.

For ad-hoc metric queries, use the Explore tab in Grafana with the Prometheus data source. Start with `rate({metric_name}[5m])` for any counter metric to see the per-second rate over the last 5 minutes.

### Logs (Loki + Grafana)

Your service's logs are available in Grafana's Explore tab using the Loki data source. The simplest query to start with is `{service="your-service-name"}` to see all recent log lines.

Add `| json` to parse structured log fields, then add filters like `| level="error"` to narrow to error logs. During an incident, filter by `trace_id` to follow a single request's log trail across services.

### Traces (Jaeger)

Open the Jaeger UI and search by service name and time range to find recent traces. Traces show you the full journey of a request: which services it touched, how long each hop took, and which span failed if there was an error.

During incident investigation, copy a `trace_id` from an error log and paste it directly into the Jaeger search to jump straight to the failing trace.

## Common Starting Points for On-Call

When a PagerDuty alert fires, open the runbook linked in the alert. The runbook tells you exactly which dashboard to look at and which queries to run. If you're investigating without a specific alert, start with the service overview dashboard to get oriented before diving into logs or traces.

## Next Steps

- Review the Alert Escalation Policy to understand your response obligations as an on-call engineer
- Familiarize yourself with the runbooks for the services you are on-call for
- Read the Writing Effective Prometheus Queries guide to improve your ad-hoc query skills
