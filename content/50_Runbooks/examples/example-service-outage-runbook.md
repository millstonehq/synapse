---
id: service-outage-runbook
type: runbook
title: Service Outage (Payments API)
status: draft
owner: On-call Engineer
created: '2025-10-18T19:48:03.153Z'
updated: '2025-10-18T19:48:03.153Z'
tags:
  - runbook
summary: Diagnose and remediate outages impacting the Payments API.
example: true
---

## Service

- [[payments-api-system]]

## Alerts

- 5xx error rate exceeds threshold
- P95 latency above 1s for 5 minutes


## Diagnosis Steps

1. Check production status dashboard and recent deploys
1. Inspect service logs for elevated error signatures
1. Verify database connectivity and latency
1. Check upstream dependencies health


## Remediation Steps

1. Rollback the last deployment if errors correlate with deploy
1. Scale up replicas by 2x temporarily
1. Clear connection pool and restart pods if stuck


## Escalation

Page the on-call SRE; notify


## Dashboards

- https://grafana.example.com/d/payments-overview
- https://kibana.example.com/app/discover#/payments
