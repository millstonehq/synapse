---
id: POSTMORTEM-039
type: postmortem
title: Grafana Authentication Failure 2024-11-05
status: approved
owner: Incident Commander
created: '2025-05-01T15:20:13.283Z'
updated: '2025-07-03T16:47:13.381Z'
tags:
  - postmortem
  - monitoring-stack
summary: Grafana Authentication Failure 2024-11-05
incident_number: INC-740
severity: SEV-1
incident_date: '2025-04-01'
detection_time: '2026-08-22T12:12:18.030Z'
resolution_time: '2024-09-19T01:51:33.242Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-073
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 5, 2024, Grafana became inaccessible to all engineers for approximately 1 hour when an OAuth2 client secret used for SSO authentication expired without warning. All engineers attempting to log in to Grafana received a 401 error from the identity provider. Because Grafana was the primary incident investigation tool, the authentication failure significantly hampered the on-call team's ability to respond to a concurrent SEV-3 alert that fired during the outage window. The root cause was an untracked OAuth2 client secret with a 90-day expiry that had no renewal reminder or monitoring.

## Timeline

- **08:42** - OAuth2 client secret for Grafana SSO expires silently
- **08:44** - First engineer reports inability to log in to Grafana; receives OAuth2 error from identity provider
- **08:47** - On-call acknowledges; confirms all engineers are locked out of Grafana
- **08:50** - Team attempts Grafana restart (no effect — secret is expired, not a service issue)
- **09:00** - Root cause identified: OAuth2 client secret expiry confirmed via identity provider admin console
- **09:05** - New client secret generated; Grafana configuration updated via Kubernetes Secret
- **09:10** - Grafana pods restarted to pick up new secret
- **09:18** - Authentication restored; all engineers can log in
- **09:42** - Incident closed; postmortem scheduled

## Impact

- **Duration**: ~1 hour of Grafana inaccessibility (08:42-09:18 UTC)
- **Users affected**: All engineers — complete loss of dashboard visibility during the window
- **Concurrent incident impact**: A SEV-3 alert for the Distributed Tracing Platform fired at 08:55 during the Grafana outage; response was delayed by 12 minutes due to lack of dashboard access
- **Data loss**: None — metric data continued to ingest normally; only the visualization layer was unavailable

## Root Cause Analysis

1. **Untracked secret expiry**: The OAuth2 client secret was created 90 days prior with a fixed expiry. There was no entry in the secrets rotation tracker, no calendar reminder, and no monitoring alert for approaching expiry. The expiry was simply forgotten.

2. **No Grafana authentication monitoring**: There was no synthetic monitoring probe testing Grafana login flow. If a probe had been running, the expiry would have been detected at 08:42 and an alert would have fired immediately rather than waiting for an engineer to notice.

## Resolution

1. Generated a new OAuth2 client secret from the identity provider admin console
2. Updated the `grafana-oauth-secret` Kubernetes Secret with the new value
3. Rolled Grafana pods to pick up the updated secret
4. Verified authentication restored for multiple test accounts

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add all monitoring-stack OAuth2 secrets to secrets rotation tracker | SRE | P1 | 2024-11-08 | Completed |
| Set 30-day and 7-day expiry reminder alerts for all OAuth2 client secrets | SRE | P1 | 2024-11-12 | Completed |
| Deploy Grafana synthetic login probe with alerting | Monitoring Eng | P2 | 2024-11-20 | Completed |
| Set OAuth2 client secret to 1-year expiry (rotate annually) | SRE | P2 | 2024-11-15 | Completed |
| Add Grafana auth failure runbook section | On-call | P3 | 2024-11-30 | Completed |

## Lessons Learned

- **What went well**: Root cause was identified quickly (13 minutes) once engineers stopped trying to restart Grafana and checked the identity provider logs.
- **What went poorly**: The lack of Grafana authentication monitoring meant a synthetic probe was not catching the failure at the moment it happened. The concurrent SEV-3 response was hampered by loss of dashboard access.
- **What was lucky**: The expiry happened during business hours with multiple engineers available. An after-hours expiry with a concurrent SEV-1 would have been significantly more impactful.
