---
id: GUIDE-047
type: guide
title: Defining SLOs for Your Service
status: approved
owner: Engineering Team
created: '2025-09-20T12:54:06.362Z'
updated: '2025-11-22T22:06:26.914Z'
tags:
  - guide
  - monitoring-stack
summary: Defining SLOs for Your Service
audience: partner
related_systems:
  - SYSTEM-040
  - SYSTEM-039
related_sops:
  - SOP-077
  - SOP-074
example: true
---

## Why SLOs Are Worth the Effort

SLOs answer the question: "How reliable does our service actually need to be?" Without SLOs, reliability conversations devolve into "make it as reliable as possible" — which is not actionable. SLOs give you a specific target to measure against, and the error budget they imply tells you when to slow down feature development and invest in reliability instead.

This guide walks you through picking good SLIs, setting realistic SLO targets, and wiring everything up in the monitoring stack.

## Step 1: Choose Your SLIs

A Service Level Indicator is a specific metric that measures user-facing reliability. The best SLIs are request-based ratios: good events / total events. Start with these four:

- **Availability**: percentage of requests that return a successful response (non-5xx)
- **Latency**: percentage of requests that complete within a defined threshold (e.g., 99% under 500ms)
- **Throughput**: percentage of time the service is processing at expected volume (optional, for async services)
- **Correctness**: percentage of responses containing the correct data (for critical data pipelines)

For most services, start with availability and latency SLIs. Add more only when there's a clear customer need.

## Step 2: Set Realistic Targets

Your SLO target should reflect the reliability users actually experience, not the theoretical maximum. Look at your last 90 days of data:

```promql
# Availability for the last 90 days
(
  sum(increase(http_server_request_total{service="your-svc", status!~"5.."}[90d]))
  /
  sum(increase(http_server_request_total{service="your-svc"}[90d]))
) * 100
```

Set your initial target at your current 90-day performance minus a small margin (e.g., if you ran at 99.7%, set the SLO at 99.5%). You can tighten it later once you have more data.

## Step 3: Calculate Your Error Budget

The error budget is how much unreliability you are allowed in a rolling 30-day window. Formula:

```
error_budget_minutes = (1 - SLO_target) * 30 * 24 * 60
```

At 99.5% availability: `0.005 * 43,200 = 216 minutes` of allowed downtime per 30 days.

Publish this number to your team. When the error budget is more than 50% consumed, slow down risky deployments. When it's exhausted, freeze features and work on reliability.

## Step 4: Wire It Up in the Monitoring Stack

Define your SLI as a Prometheus recording rule so it is efficiently queryable. Then register the SLO in the platform's SLO tracking system, which will create error budget burn rate alerts automatically.

Contact the Platform team to have your SLO registered. Provide: the SLI query, the SLO target, the service name, and the team owner.

## Common Mistakes to Avoid

**Do not set SLOs without looking at real data.** Aspirational targets that you cannot currently meet create alert fatigue from day one.

**Do not include maintenance windows in your SLO measurement.** Use AlertManager silences during planned maintenance and configure your SLI query to exclude maintenance window events.

**Do not define too many SLOs.** Start with one or two per service. More SLOs dilute focus. Add more only when you have a specific reliability question a new SLO would answer.

## Next Steps

- Review the SLO Definition Policy for mandatory requirements around SLO governance
- Read the SLI/SLO Definition Standard for technical requirements on SLI queries
- Schedule a quarterly SLO review using the SLO Review and Update Process
