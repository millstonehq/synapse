---
id: POSTMORTEM-020
type: postmortem
title: Notification Queue Overflow 2025-03-05
status: proposed
owner: Incident Commander
created: '2024-04-27T13:05:56.458Z'
updated: '2026-08-21T08:34:44.907Z'
tags:
  - postmortem
  - notification-service
summary: Notification Queue Overflow 2025-03-05
incident_number: INC-361
severity: SEV-1
incident_date: '2024-02-06'
detection_time: '2024-05-14T19:10:42.495Z'
resolution_time: '2024-11-28T10:15:06.918Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-034
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 5, 2025, the Notification Platform's RabbitMQ queue for the LOW priority channel overflowed during a large marketing campaign batch send, causing approximately 1.1 million LOW-priority notifications to be dropped when the queue hit its configured maximum depth. The campaign owner had not coordinated the batch send volume with the Notification Platform team, and the queue depth limit had not been increased to accommodate the expected volume.

HIGH and CRITICAL priority queues were unaffected. Transactional notifications continued processing normally throughout the incident. The dropped LOW-priority notifications were campaign messages and did not have a direct user-harm impact, but the campaign reach was reduced by 31%.

## Timeline

- **08:00** - Marketing team initiates a batch campaign send of 3.5 million LOW-priority push notifications
- **08:00** - LOW priority RabbitMQ queue begins filling rapidly
- **08:11** - LOW priority queue depth reaches 500,000 (100% capacity). RabbitMQ begins dropping messages
- **08:12** - `notification_queue_at_capacity` alert fires. On-call acknowledges
- **08:15** - On-call identifies the batch campaign as the source. Contacts marketing team to pause the send
- **08:22** - Marketing team pauses the batch send
- **08:23** - Queue depth begins declining as consumers process existing messages
- **09:04** - Queue drained to normal depth
- **09:15** - Incident formally closed

## Impact

- **Duration**: ~1 hour (08:00 - 09:04 UTC) until queue cleared
- **Notifications dropped**: ~1.1 million LOW-priority campaign push notifications
- **Campaign reach**: Reduced from 3.5M target to ~2.4M delivered
- **User impact**: No user harm; affected notifications were marketing/promotional
- **SLA impact**: LOW-priority notification delivery SLA breached for the campaign batch

## Root Cause Analysis

1. **No campaign volume coordination process**: The marketing team had no process for coordinating large batch sends with the Notification Platform team. The platform's LOW-priority queue capacity (500,000 messages) was not documented in any marketing team workflow, and the campaign was launched without knowledge of the constraint.

2. **Fixed queue capacity without backpressure**: The RabbitMQ LOW-priority queue was configured with a hard maximum depth and no backpressure mechanism to slow producers when the queue approached capacity. When the limit was reached, messages were silently dropped rather than returning an error to the campaign sender.

## Resolution

1. Marketing team paused the batch send after being contacted by on-call
2. Monitored queue drain until normal depth was restored
3. Remaining campaign messages were re-queued after capacity was confirmed available
4. Coordinated the re-send to use the rate-limited campaign send API to avoid a second overflow

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement producer backpressure: return 429 when LOW queue is at 80% capacity | Notification Engineering | P1 | 2025-03-12 | Completed |
| Add queue depth alert at 70% capacity (before overflow) | SRE | P1 | 2025-03-10 | Completed |
| Create campaign batch send intake process requiring Notification Platform sign-off for sends > 500K | Notification Engineering | P2 | 2025-03-19 | In progress |
| Increase LOW-priority queue capacity to 2M messages | SRE | P2 | 2025-03-19 | Completed |
| Document queue capacities in the Notification Platform integration guide | Notification Engineering | P3 | 2025-03-31 | Pending |

## Lessons Learned

- **What went well**: HIGH and CRITICAL queues were completely unaffected. Isolation between priority queues worked as designed.
- **What went poorly**: Silent message drops were invisible to the campaign sender. There was no feedback loop indicating that messages were being lost.
- **What was lucky**: The dropped messages were low-priority marketing content with no user safety or compliance implications.
