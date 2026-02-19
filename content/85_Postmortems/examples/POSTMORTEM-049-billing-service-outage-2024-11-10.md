---
id: POSTMORTEM-049
type: postmortem
title: Billing Service Outage 2024-11-10
status: accepted
owner: On-Call Engineer
created: '2024-11-26T07:50:07.870Z'
updated: '2025-05-05T14:03:07.848Z'
tags:
  - postmortem
  - billing-engine
summary: Billing Service Outage 2024-11-10
incident_number: INC-930
severity: SEV-4
incident_date: '2025-01-04'
detection_time: '2024-02-07T04:53:06.300Z'
resolution_time: '2026-03-22T00:21:38.753Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-096
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 10, 2024, the Billing Engine experienced a 15-minute outage affecting all billing services. A Kubernetes node failure in the production cluster caused the RabbitMQ pod to be evicted and fail to reschedule due to a misconfigured node affinity rule that required a node label that no longer existed. With RabbitMQ unavailable, the Billing Event Processor could not consume events, causing invoice generation, tax calculation triggers, and notification dispatches to queue up.

The incident was detected by alerting at 09:12 UTC and resolved at 09:27 UTC when the node affinity misconfiguration was identified and corrected, allowing RabbitMQ to reschedule successfully.

## Timeline

- **09:08** - Kubernetes node `billing-node-03` enters NotReady state due to a hardware issue in the cloud provider
- **09:09** - RabbitMQ pod evicted from `billing-node-03` by Kubernetes node pressure eviction
- **09:10** - RabbitMQ attempts to reschedule but fails: node affinity rule requires label `billing-tier=critical` which was removed from all nodes during a maintenance operation on November 8
- **09:12** - `rabbitmq_pod_not_running` alert fires. On-call engineer acknowledges.
- **09:15** - Billing Event Processor consumers lose connection to RabbitMQ; dead letter queue begins accumulating
- **09:17** - On-call confirms RabbitMQ pod is in `Pending` state; checks pod describe output and sees node affinity scheduling failure
- **09:20** - On-call applies emergency patch removing the outdated node affinity constraint from the RabbitMQ deployment
- **09:22** - RabbitMQ pod schedules and starts successfully on an available node
- **09:25** - Billing Event Processor consumers reconnect; event processing resumes
- **09:27** - Dead letter queue drained; all queued events processed. Incident closed.

## Impact

- **Duration**: ~15 minutes (09:12 - 09:27 UTC)
- **Customers affected**: No direct customer impact; billing operations were delayed but no invoices were lost
- **Revenue impact**: Estimated $12,000 in delayed invoice processing (not revenue loss — invoices were generated after recovery)
- **SLA impact**: Billing Engine availability SLA missed for November (99.97% vs 99.99% target)
- **Customer communications**: No customer communication required; invoice delivery remained within SLA

## Root Cause Analysis

1. **Stale node affinity label on RabbitMQ deployment**: A November 8 infrastructure maintenance operation removed the `billing-tier=critical` node label from all Kubernetes nodes as part of a label taxonomy cleanup. The RabbitMQ deployment still had a required node affinity rule referencing this label, but this was not caught because RabbitMQ was running on a node with the label at the time of removal.

2. **No validation of node affinity rules against active node labels**: The maintenance runbook for node label changes had no step to check whether any running workloads reference the labels being removed. The stale affinity rule went undetected until the pod was evicted.

## Resolution

1. Applied an emergency patch to the RabbitMQ deployment removing the stale node affinity constraint
2. Verified RabbitMQ rescheduled successfully and consumers reconnected
3. Drained the dead letter queue backlog accumulated during the 15-minute outage

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add pre-flight check to node label maintenance runbook: query all pods with nodeAffinity referencing the label to be removed | Platform SRE | P1 | 2024-11-17 | Completed |
| Remove all stale `billing-tier` node affinity rules from billing service deployments | Billing Engineering | P1 | 2024-11-15 | Completed |
| Add Kubernetes admission webhook that warns when nodeAffinity references a non-existent label | Platform SRE | P2 | 2024-12-01 | In progress |
| Update RabbitMQ deployment to use pod anti-affinity instead of required nodeAffinity | Billing Engineering | P2 | 2024-11-30 | Pending |

## Lessons Learned

- **What went well**: Alerting fired within 4 minutes of the RabbitMQ eviction. On-call correctly identified the scheduling failure from pod describe output and had the fix deployed within 10 minutes of escalation.
- **What went poorly**: The maintenance runbook for node label changes had no safety check for workloads referencing the labels being removed. A 2-day gap between the label removal and the node failure meant the stale affinity rule was not immediately visible.
- **What was lucky**: The duration was only 15 minutes because the fix was a simple label removal rather than requiring a node restart or data recovery.
