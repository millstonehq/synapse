---
id: SOP-040
type: sop
title: Notification Queue Drain SOP
status: approved
owner: DevOps Lead
created: '2025-07-17T09:27:52.025Z'
updated: '2025-04-12T01:41:41.332Z'
tags:
  - sop
  - notification-service
summary: Notification Queue Drain SOP
related_process: PROCESS-064
related_systems:
  - SYSTEM-016
example: true
---

## Preconditions

- A decision has been made to intentionally drain the notification queue (e.g., before a major configuration change, after a channel disable, or to clear a backlog of expired messages)
- The scope of the drain is defined: which queue(s), which message types, and whether messages should be discarded or requeued
- Platform Lead has approved the drain operation
- The on-call engineer is monitoring during the operation

## Materials/Access

- Queue management console (AWS SQS, RabbitMQ management UI, or equivalent) with message purge and DLQ access
- Notification Service admin API with queue management endpoints
- Monitoring dashboard to track queue depth in real time
- Slack access to `#notifications-ops`

## Procedure

1. Post in `#notifications-ops`: "Starting notification queue drain. Queue: [name]. Reason: [brief description]. Approved by: [Platform Lead name]."
2. Pause the notification queue consumer to stop active processing while the drain is prepared.
3. Take a snapshot of current queue depth and message age distribution for the operations record.
4. Determine the disposition for queued messages: messages older than the TTL should be discarded; unexpired messages may need to be requeued or held.
5. If discarding expired messages: purge the queue using the queue management console's purge function and confirm queue depth returns to zero.
6. If requeuing unexpired messages: use the DLQ re-drive policy or manual re-drive to move messages to a holding queue for later processing.
7. Resume the notification queue consumer once the queue contains only valid, processable messages.
8. Monitor queue depth and consumer processing rate for 15 minutes post-drain to confirm normal operation.
9. Update the operations ticket with the drain result: messages discarded, messages requeued, final queue depth.

## Validation

- Queue depth matches the expected post-drain value (zero for full purge, or reduced to unexpired messages only)
- Consumer is processing messages normally with no error spikes
- Monitoring dashboard shows queue depth trending toward zero or holding at the expected level

## Rollback

1. If the drain was initiated in error and messages with delivery value were discarded, assess whether the originating events can be replayed from the event source.
2. Contact the owning service team to re-trigger notification events for affected users if replay is possible.
3. Document the scope of the erroneous drain in the incident ticket and conduct a post-incident review.
