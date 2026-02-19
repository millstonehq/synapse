---
id: GUIDE-033
type: guide
title: Kafka Producer Best Practices Guide
status: approved
owner: Developer Experience
created: '2024-05-02T14:44:14.685Z'
updated: '2025-03-08T04:07:32.236Z'
tags:
  - guide
  - data-pipeline
summary: Kafka Producer Best Practices Guide
audience: partner
related_systems:
  - SYSTEM-029
  - SYSTEM-027
related_sops:
  - SOP-053
  - SOP-056
example: true
---

## Why Producer Quality Matters

Kafka producers are the entry point for all event data into the platform. A poorly configured producer can cause message loss, duplicate events, consumer compatibility failures, or broker overload. Because many consumers depend on the same topics, a misbehaving producer has a wide blast radius. Following these best practices protects both your own consumers and every other team reading your topic.

## Schema and Compatibility

Before your producer publishes its first message in production, the schema must be registered in the schema registry:

- Register the Avro or Protobuf schema for your event type before deploying the producer
- Configure the producer serializer to use the schema registry: `schema.registry.url`
- Set the compatibility mode to `BACKWARD_COMPATIBLE` so future schema versions do not break existing consumers
- Never remove or rename required fields without a formal schema evolution process and consumer sign-off

## Producer Configuration Essentials

These configuration settings are required for all production Kafka producers:

- `acks=all` — ensures the message is acknowledged by all in-sync replicas before the producer considers it delivered, preventing message loss on broker failure
- `enable.idempotence=true` — eliminates duplicate messages caused by producer retries; requires `acks=all`
- `retries` — set to a high value (e.g., `Integer.MAX_VALUE`) in combination with idempotence; let the producer retry rather than dropping messages
- `compression.type=snappy` or `lz4` — reduces network bandwidth and broker disk usage; required for high-throughput topics
- `max.in.flight.requests.per.connection=5` — safe maximum when idempotence is enabled

## Partitioning Strategy

The partition key determines how messages are distributed and affects consumer parallelism and ordering:

- Use a business entity key (e.g., `user_id`, `order_id`) as the partition key when message ordering per entity matters
- Avoid high-cardinality UUID keys that distribute messages randomly if you need ordered processing per entity
- Avoid using `null` keys for topics with multiple partitions — null-keyed messages are round-robin distributed, breaking ordering guarantees
- Do not change the partitioning strategy for an existing topic without coordinating with all consumers

## Error Handling and Observability

Producers must handle errors gracefully and expose metrics:

- Implement a dead-letter topic for messages that fail serialization or validation — do not silently drop them
- Emit producer metrics to the central metrics store: message rate, error rate, and batch size
- Log the topic name and schema ID with every publish attempt at debug level for traceability
- Set up an alert for sustained producer error rates above 0.5%

## Next Steps

- Review the Event Schema Registry Standard for registration requirements
- Test producer and consumer compatibility in staging before deploying to production
- Add producer metrics to the pipeline monitoring dashboard per the Data Pipeline Monitoring Standard

## How Our Pipeline Works

### Build and Test

When you merge a PR to `main`, CI automatically:

- Runs the full test suite (unit, integration, E2E)
- Builds a Docker image tagged with the commit SHA
- Pushes the image to our container registry
- Generates a deployment manifest

You don't need to do anything here. If CI fails, the merge is blocked.

### The Change Ticket

Before deploying, you need an approved change ticket. This isn't bureaucracy - it's how we:

- Track what changed and why (audit trail)
- Ensure someone besides you reviewed the risk
- Coordinate timing so deploys don't collide

For low-risk changes (config updates, small bug fixes), approval is lightweight - your PR reviewer can approve the ticket. For high-risk changes (database migrations, new services, breaking API changes), you need a senior engineer's sign-off.

### The Deploy Itself

We use blue-green deployments. This means:

- The new version spins up alongside the old one
- Health checks verify the new version is healthy
- Traffic gradually shifts from old to new
- If anything looks wrong, traffic shifts back instantly

The key insight: **rollback is always one click away**. You don't need to "fix forward" under pressure. If metrics degrade, roll back first, investigate second.

### Monitoring Window

After a deploy, we watch metrics for 15 minutes:

- **Error rate**: Should stay below 0.1%. Any spike above 1% triggers rollback.
- **Latency**: P95 should stay under 500ms. Sustained increase above 1s triggers rollback.
- **Business metrics**: Order completion rate, payment success rate should stay stable.

If you're unsure whether a metric looks normal, check the dashboards linked in the [[example-service-outage-runbook|Service Outage Runbook]] for baseline comparisons.

## Common Questions

### "Can I deploy on Friday afternoon?"

We have a soft freeze Friday after 3pm. You can deploy with senior engineer approval, but ask yourself: do you want to be debugging at 7pm on a Friday?

### "What if my change needs a database migration?"

Database migrations are always high-risk. They need:
- A tested rollback migration
- Off-peak deployment window
- DBA review for anything touching indexes or large tables

See the database migration section of the [[example-production-deployment-sop|Deployment SOP]] for the exact procedure.

### "How do I know if my change is high-risk?"

If any of these are true, it's high-risk:
- Database schema changes
- New external service dependencies
- Changes to authentication or authorization
- Breaking API changes (even behind feature flags)
- Infrastructure changes (new queues, new caches, scaling config)

## Next Steps

- Read the [[example-change-management-process|Change Management Process]] to understand the governance workflow
- Bookmark the [[example-production-deployment-sop|Production Deployment SOP]] for when you're ready to deploy
- Familiarize yourself with the [[example-service-outage-runbook|Service Outage Runbook]] before your first on-call rotation
