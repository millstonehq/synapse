---
id: POSTMORTEM-041
type: postmortem
title: Customer Portal Outage 2025-02-01
status: approved
owner: On-Call Engineer
created: '2025-05-21T06:03:04.412Z'
updated: '2025-07-14T01:06:59.952Z'
tags:
  - postmortem
  - customer-portal
summary: Customer Portal Outage 2025-02-01
incident_number: INC-832
severity: SEV-2
incident_date: '2026-09-19'
detection_time: '2025-06-27T04:21:17.610Z'
resolution_time: '2026-05-03T07:13:45.515Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-085
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 1, 2025, the Customer Portal experienced a 2-hour 14-minute full outage caused by a Kubernetes node pool upgrade that was executed without the required rolling-replacement configuration. The upgrade terminated all portal pods simultaneously, leaving zero healthy replicas serving traffic. All portal pages returned 503 errors for the duration.

The incident was detected by on-call alerting at 09:14 UTC and resolved at 11:28 UTC when a new node pool was provisioned and portal pods rescheduled. Approximately 1,400 customers were unable to access the portal during the outage window.

## Timeline

- **09:10** - Platform team begins Kubernetes node pool upgrade for the portal namespace without notifying on-call
- **09:12** - All portal pods are evicted as nodes are drained; new nodes are not yet ready
- **09:14** - `portal_availability_zero` alert fires. On-call engineer acknowledges
- **09:18** - On-call checks recent portal deploys; no portal deploy in last 48 hours
- **09:22** - On-call identifies zero healthy pods. Attempts `kubectl rollout restart` — no nodes available to schedule pods
- **09:35** - On-call escalates to platform team lead and portal tech lead
- **09:50** - Platform team identifies root cause: node pool upgrade drained all nodes before new nodes were ready
- **10:15** - New node pool provisioned and nodes join the cluster
- **11:05** - Portal pods successfully scheduled and pass readiness probes
- **11:28** - Traffic restored; incident declared resolved after 20-minute stable observation window

## Impact

- **Duration**: 2 hours 14 minutes (09:14 - 11:28 UTC)
- **Users affected**: ~1,400 customers who attempted portal access during the window
- **Functions affected**: All portal pages, support ticket submission, preference management
- **SLA impact**: Monthly availability dropped to 99.91% (below 99.95% target)
- **Customer communications**: Status page updated at 09:30; 47 support tickets received

## Root Cause Analysis

1. **Missing PodDisruptionBudget**: The portal namespace had no PodDisruptionBudget configured, allowing the node pool upgrade to evict all pods simultaneously rather than one at a time.

2. **No pre-upgrade notification**: The platform team's node upgrade runbook did not require notification to application on-call teams before performing node pool operations. This meant the portal on-call had no warning.

## Resolution

1. Provisioned a replacement node pool with correct sizing
2. Waited for new nodes to reach Ready state
3. Confirmed portal pods scheduled and passing readiness probes
4. Monitored for 20 minutes before closing the incident

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add PodDisruptionBudget to portal namespace (minAvailable: 2) | Platform team | P1 | 2025-02-08 | Completed |
| Update node upgrade runbook to require app team notification | Platform team | P1 | 2025-02-08 | Completed |
| Add node pool upgrade to portal change freeze criteria | Engineering Manager | P2 | 2025-02-15 | In progress |
| Add `portal_pod_count_zero` alert with immediate page | SRE | P2 | 2025-02-15 | Completed |

## Lessons Learned

- **What went well**: Alerting fired within 2 minutes of the outage starting. Escalation to the platform team was fast once the node-level root cause was suspected.
- **What went poorly**: No PodDisruptionBudget meant a routine infrastructure operation caused a complete outage. This was entirely preventable.
- **What was lucky**: The outage occurred at 09:14 UTC (early morning for most users), limiting customer impact compared to peak hours.
