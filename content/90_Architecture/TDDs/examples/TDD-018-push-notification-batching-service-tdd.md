---
id: TDD-018
type: tdd
title: Push Notification Batching Service TDD
status: review
owner: Principal Engineer
created: '2024-07-28T03:24:08.269Z'
updated: '2025-03-02T12:41:16.475Z'
tags:
  - tdd
  - notification-service
summary: Push Notification Batching Service TDD
related_adrs:
  - ADR-0014
  - ADR-0016
example: true
---

## Summary

Design the Push Notification Batching Service — a component of the Push Notification Gateway that aggregates individual push notification dispatch requests into platform-optimized batch payloads before submission to APNs and FCM. The batching service must reduce provider API call volume by 60% compared to individual sends while maintaining sub-2s delivery latency for HIGH and CRITICAL priority notifications.

This design uses FCM as the Android delivery layer per [[ADR-0016|ADR-0016: Use Firebase for Push Notifications]] and consumes from the RabbitMQ priority queues defined in [[ADR-0014|ADR-0014: Choose RabbitMQ for Notification Queue]].

## Overview

The batching service sits between the RabbitMQ consumer and the platform provider adapters. It accumulates messages from the queue into time-windowed batches and submits them to FCM (up to 500 tokens per call) or APNs (one connection, pipelined HTTP/2 requests) as appropriate.

Key design principles:
- **Priority-aware batching**: CRITICAL and HIGH notifications are dispatched immediately (no batching window). NORMAL and LOW notifications are batched in 500ms windows.
- **Platform separation**: iOS (APNs) and Android (FCM) batches are built and submitted independently. A batch is never mixed across platforms.
- **Partial failure handling**: If a batch submission returns partial failures (some tokens invalid, some successful), the service processes each token's result independently and updates the token registry for invalid tokens.
- **Backpressure awareness**: If the provider rate limit is approached, the batching window is extended to reduce submission frequency rather than dropping messages.

## Architecture

- **Priority Router**: Reads notifications from the priority-specific RabbitMQ queue. Immediately dispatches CRITICAL/HIGH messages; buffers NORMAL/LOW messages in the batch accumulator.
- **Batch Accumulator**: Time-windowed accumulator per platform. Flushes when the batch reaches 500 entries (FCM max) or the window expires (500ms), whichever comes first.
- **FCM Batch Submitter**: Calls the FCM v1 `batchSend` endpoint. Processes the multicast response to identify successful tokens, invalid tokens, and rate limit signals.
- **APNs Pipeline Submitter**: Sends individual APNs HTTP/2 requests over a persistent connection. Uses HTTP/2 multiplexing to achieve high throughput without per-request connection overhead.
- **Token Registry Updater**: After each batch, marks invalid/unregistered tokens as inactive in the SQL Server token registry.

## Information Model

- **PushJob**: `notificationId`, `platform` (ios|android), `deviceToken`, `title`, `body`, `data{}`, `priority`, `apnsExpiry`, `fcmCollapseKey`, `dequeuedAt`
- **PushBatch**: `platform`, `jobs[]`, `createdAt`, `submittedAt`
- **BatchResult**: `batchId`, `successCount`, `failureCount`, `invalidTokens[]`, `retryableFailures[]`, `submittedAt`

## Interfaces

- `BatchAccumulator.add(job: PushJob) → void` — Add a job to the active batch window
- `BatchAccumulator.flush() → PushBatch` — Force flush the current batch (used for priority routing)
- `FCMBatchSubmitter.submit(batch: PushBatch) → BatchResult`
- `APNsPipelineSubmitter.submit(batch: PushBatch) → BatchResult`
- `TokenRegistryUpdater.markInvalid(tokens: string[]) → void`

## Files and Layout

```
src/
  consumers/
    push-job.consumer.ts          - RabbitMQ consumer; routes to priority dispatcher
  batching/
    priority-router.ts            - CRITICAL/HIGH immediate dispatch vs NORMAL/LOW buffering
    batch-accumulator.ts          - Time-windowed batch builder
  providers/
    fcm-batch-submitter.ts        - FCM v1 batchSend integration
    apns-pipeline-submitter.ts    - APNs HTTP/2 pipeline integration
  registry/
    token-registry-updater.ts     - SQL Server token invalidation
  types/
    push-job.ts
    push-batch.ts
    batch-result.ts
```

## Work Plan

1. **Phase 1 - Foundation (Week 1)**: Define types, RabbitMQ consumer scaffolding, token registry updater
2. **Phase 2 - Batch Accumulator (Week 2)**: Time-windowed accumulator with configurable window size and max batch size, flush triggers
3. **Phase 3 - FCM Integration (Week 3)**: FCM v1 batchSend, multicast response processing, partial failure handling
4. **Phase 4 - APNs Integration (Week 4)**: APNs HTTP/2 persistent connection, pipelined request submission, error response handling
5. **Phase 5 - Priority Routing (Week 5)**: CRITICAL/HIGH bypass of batching window, end-to-end latency validation
6. **Phase 6 - Load Testing (Week 6)**: Validate 60% API call reduction target, confirm sub-2s latency for HIGH priority

## Risks and Mitigations

- **Risk**: FCM v1 batchSend API changes break the batch submission path. **Mitigation**: Pin FCM SDK version; subscribe to Firebase changelog; run nightly integration tests against FCM sandbox.
- **Risk**: APNs persistent connection drops under low traffic and causes latency spikes on reconnect. **Mitigation**: Implement connection keepalive pings; reconnect proactively on connection age > 30 minutes.
- **Risk**: Batch accumulator window causes NORMAL priority notification latency to exceed 500ms SLA during low-volume periods. **Mitigation**: Flush immediately when batch has only 1 entry and the window has elapsed, rather than waiting for the next entry.
