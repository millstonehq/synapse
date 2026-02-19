---
id: ADR-0014
type: adr
title: Choose RabbitMQ for Notification Queue
status: accepted
owner: Tech Lead
created: '2024-02-20T06:38:57.737Z'
updated: '2026-01-06T12:49:50.298Z'
tags:
  - adr
  - notification-service
summary: Choose RabbitMQ for Notification Queue
example: true
---

## Context

The Notification Platform needs a message queue to decouple notification producers from delivery services. Notification producers (order service, auth service, marketing tools) need to enqueue notifications and immediately return to their own workflows; the actual delivery to email, push, and SMS channels must happen asynchronously.

Key requirements for the queue system include: support for multiple priority levels with independent consumer groups, durable message storage to prevent notification loss during service restarts, dead-letter queuing for failed notifications, and the ability to inspect and replay messages for debugging. The expected steady-state throughput is approximately 200,000 notifications per day with peaks of 500 messages/second during campaign blasts.

The team has existing operational experience with RabbitMQ and Kafka. Both are available on our managed infrastructure. Redis Streams was considered as a lightweight alternative.

## Decision

We will use **RabbitMQ** as the notification queue for the Notification Platform.

We will create four separate exchanges corresponding to the four priority levels (CRITICAL, HIGH, NORMAL, LOW), each with a dedicated queue and a corresponding dead-letter exchange. Consumer groups are independently scalable per priority level. The routing engine will publish to the appropriate exchange based on the notification's priority field.

## Consequences

**Positive:**
- Per-priority queues allow CRITICAL and HIGH notifications to continue processing without contention from LOW-priority bulk sends
- Dead-letter queues provide a natural holding area for failed notifications, enabling replay without re-triggering the originating event
- RabbitMQ's management UI allows on-call engineers to inspect queue depth and message contents without writing custom tooling
- Existing team familiarity reduces operational ramp-up time

**Negative:**
- RabbitMQ's throughput ceiling is lower than Kafka's; at very high volumes (>10,000 msg/sec sustained) we may need to revisit
- Managed RabbitMQ adds ~$800/month to infrastructure costs
- RabbitMQ clustering and failover requires more operational attention than Kafka's partition replication model

**Neutral:**
- Message ordering within each priority queue is preserved (FIFO), which is sufficient for notifications; strict cross-queue ordering is not required

## Alternatives Considered

**Kafka:**
- Pro: Higher throughput ceiling, log-compaction for replay, mature ecosystem
- Con: Topic-per-priority model is operationally heavier; Kafka's consumer group model makes per-priority scaling more complex than RabbitMQ's queue-per-priority approach; team has less Kafka operational experience
- Rejected because: The added complexity is not justified by our throughput requirements, and the team's RabbitMQ familiarity reduces incident response time

**Redis Streams:**
- Pro: Zero additional infrastructure cost (Redis already in use for caching), simple API
- Con: No native dead-letter queue support; persistence is append-only with manual consumer acknowledgment; limited tooling for queue inspection; no exchange/routing concept for priority separation
- Rejected because: Missing dead-letter queue support is a significant gap for a notification system where failed delivery tracking is a core requirement
