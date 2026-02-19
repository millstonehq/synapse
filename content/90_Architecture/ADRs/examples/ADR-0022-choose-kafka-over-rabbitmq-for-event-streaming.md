---
id: ADR-0022
type: adr
title: Choose Kafka Over RabbitMQ for Event Streaming
status: approved
owner: Principal Engineer
created: '2025-08-21T21:55:55.251Z'
updated: '2025-06-23T00:20:22.562Z'
tags:
  - adr
  - data-pipeline
summary: Choose Kafka Over RabbitMQ for Event Streaming
example: true
---

## Context

The Data Pipeline team is building a central event streaming backbone to carry high-volume operational events — order placements, inventory updates, fulfillment state transitions, and sensor telemetry — from upstream producers to downstream consumers including the analytics warehouse, the fraud detection service, and the customer notification platform. Current point-to-point integrations using HTTP webhooks and shared PostgreSQL tables have become a maintenance liability: schema coupling between teams, no replay capability, and no single audit trail for event history.

We need a durable, ordered, replayable event log that can sustain peak ingest rates of roughly 50,000 events per second while allowing multiple independent consumer groups to read the same stream at their own pace. The system must retain raw events for at least 30 days to support late-arriving consumers and backfill operations after schema changes or consumer bugs.

Operational constraints require that the chosen platform integrate with our existing Kubernetes-based infrastructure and be supportable by a small platform engineering team without specialized expertise beyond what is already present on staff. Both Apache Kafka and RabbitMQ are under active consideration and have existing community support within the team.

## Decision

We will adopt **Apache Kafka** (managed via Confluent Cloud) as the event streaming platform for the Data Pipeline domain. All inter-service event publishing will target named Kafka topics; consumer groups will be registered per service and tracked in the schema registry. Topic retention will be set to 30 days by default, with compacted topics used for entity-state streams where only the latest state per key is required.

Schema management will use the Confluent Schema Registry with Avro schemas enforced at the producer boundary. The platform team will own topic provisioning and ACL management; application teams will own schema definitions for their owned event types.

## Consequences

**Positive:**

- Log-based storage with configurable retention gives consumers full replay capability without special infrastructure — any consumer can seek to any offset at any time within the retention window.
- Consumer groups are first-class: multiple independent consumers can read the same topic without interfering with each other, eliminating the fan-out topology we currently maintain manually.
- Kafka's partition model provides horizontal throughput scaling; adding partitions allows ingest rate to grow linearly with cluster capacity.

**Negative:**

- Kafka's operational model is significantly more complex than RabbitMQ — partition assignment, consumer group rebalancing, and offset management require deeper platform knowledge and careful tuning.
- At-least-once delivery semantics require consumers to implement idempotent processing; this shifts deduplication responsibility to every consuming service.
- Confluent Cloud costs are consumption-based and will exceed RabbitMQ Cloud at our projected ingest volume; budget approval was required as part of this decision.

**Neutral:**

- Existing RabbitMQ-based integrations (primarily internal task queues for background jobs) are out of scope for this decision and will continue to run on RabbitMQ.
- Teams will need to migrate from the current PostgreSQL-based event log over a transition period; both systems will run in parallel during migration.

## Alternatives Considered

**RabbitMQ (CloudAMQP managed):**
- Pro: Lower operational overhead for small-scale use cases; team already has working RabbitMQ deployments; AMQP support simplifies integration with legacy services.
- Con: RabbitMQ is a message broker, not an event log — messages are deleted after acknowledgement, making replay and late consumer catchup impossible without custom persistence layers. Fan-out to multiple consumer groups requires manual exchange-to-queue topology management that grows fragile at scale.
- Rejected because: The absence of native replay and durable log semantics would require us to re-implement exactly the features Kafka provides, negating any simplicity advantage.

**AWS Kinesis Data Streams:**
- Pro: Fully managed by AWS with no cluster to operate; native integration with the AWS services already in use (Lambda, Firehose, S3).
- Con: 7-day maximum retention (extended retention adds cost) falls short of our 30-day requirement without additional archival infrastructure. Shard-based scaling requires manual shard splitting; partition key design is less flexible than Kafka's consumer group model for our mixed workload.
- Rejected because: The retention ceiling and the tighter AWS lock-in were not acceptable given our multi-cloud neutrality goal and the 30-day replay requirement.

**Redis Streams:**
- Pro: Extremely low latency; Redis is already deployed as a caching layer so no new infrastructure is required; simple consumer group API.
- Con: Redis Streams are memory-backed; 30-day retention at 50k events/second would require several terabytes of Redis memory, which is cost-prohibitive. Persistence guarantees are weaker than a disk-backed log.
- Rejected because: Memory cost at our target retention and ingest volume makes Redis Streams economically unviable as the primary event backbone.
