---
id: SOP-057
type: sop
title: Handle Kafka Consumer Group Rebalance SOP
status: approved
owner: DevOps Lead
created: '2024-08-02T23:39:17.450Z'
updated: '2026-04-03T08:07:17.167Z'
tags:
  - sop
  - data-pipeline
summary: Handle Kafka Consumer Group Rebalance SOP
related_process: PROCESS-035
related_systems:
  - SYSTEM-029
example: true
---

## Preconditions

- A consumer group rebalance event has been detected via alert or consumer lag spike
- The affected consumer group ID and topic are known
- It is confirmed that the rebalance is not caused by a deliberate scaling operation already in progress

## Materials/Access

- Kafka CLI tools (`kafka-consumer-groups.sh`) or administrative access to the Kafka management UI
- Access to Grafana consumer lag dashboard
- Access to the consumer application deployment platform (Kubernetes or equivalent)
- Access to #kafka-incidents Slack channel

## Procedure

1. Post in #kafka-incidents: "Consumer group [group_id] rebalance detected on topic [topic]. Investigating lag: [current_lag]."
2. Run `kafka-consumer-groups.sh --describe --group [group_id]` to see current partition assignments and consumer member status.
3. Identify which consumers dropped from the group; check consumer pod logs for the reason (heartbeat timeout, session timeout, or application error).
4. If rebalance is caused by a crashed consumer pod, confirm the pod restarts automatically via the deployment controller.
5. If rebalance is caused by excessive processing time per message, increase `max.poll.interval.ms` in the consumer configuration and redeploy.
6. Monitor the Grafana consumer lag dashboard; confirm lag is decreasing as the consumer group reassigns partitions and resumes processing.
7. If lag exceeds the alert threshold after 10 minutes, scale up the consumer group by adding additional consumer instances.
8. Confirm all partitions are assigned and no partition is unassigned in the consumer group description output.
9. Post in #kafka-incidents: "Consumer group [group_id] rebalance resolved. Lag: [current_lag]. All partitions assigned."

## Validation

- `kafka-consumer-groups.sh --describe` shows all topic partitions assigned to an active consumer
- Consumer lag is decreasing at a rate consistent with normal processing throughput
- No consumer pod restart loops are occurring (check pod restart count)
- Grafana consumer lag metric is below the alert threshold

## Rollback

1. If the consumer group is stuck in a continuous rebalance loop, pause the consumer deployment to stop new members joining.
2. Reset the consumer group offsets to the latest committed offset using `kafka-consumer-groups.sh --reset-offsets`.
3. Redeploy the consumer application with corrected configuration (session timeout, max poll interval).
4. Monitor the restarted consumer group for 10 minutes to confirm stable partition assignment.
5. If persistent rebalance issues continue, escalate to the Kafka platform team for broker-side investigation.
