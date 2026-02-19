---
id: GUIDE-035
type: guide
title: Schema Registry Development Guide
status: approved
owner: Developer Experience
created: '2024-04-23T15:23:16.225Z'
updated: '2026-07-27T02:51:45.893Z'
tags:
  - guide
  - data-pipeline
summary: Schema Registry Development Guide
audience: customer
related_systems:
  - SYSTEM-027
  - SYSTEM-028
related_sops:
  - SOP-058
  - SOP-054
example: true
---

## What the Schema Registry Does

The Schema Registry is a centralized store for versioned event schemas used across all Kafka topics. When a producer publishes an Avro or Protobuf message, it registers the schema and embeds the schema ID in the message. Consumers fetch the schema by ID to deserialize the message correctly. This allows producers and consumers to evolve independently as long as they respect compatibility rules.

Without the Schema Registry, a producer change that modifies an event payload would silently break all consumers reading that topic with no warning or error at deploy time.

## Registering a New Schema

To register a schema for a new topic before your producer goes live:

1. Define your schema as an `.avsc` (Avro Schema) or `.proto` (Protobuf) file in the pipeline repository under `schemas/`
2. Run the compatibility check: `curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data '{"schema": "<escaped_schema>"}' http://[registry]/compatibility/subjects/[topic]-value/versions/latest`
3. Register the schema: `curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data '{"schema": "<escaped_schema>"}' http://[registry]/subjects/[topic]-value/versions`
4. Note the returned schema ID and record it in the pipeline documentation
5. Configure your producer to use the schema ID: set `auto.register.schemas=false` so the producer uses only the pre-registered schema

## Compatibility Modes

The schema registry enforces compatibility rules to protect consumers from breaking changes. The organization standard is `BACKWARD_COMPATIBLE`, meaning a new schema version can be read by consumers using the previous version:

- **Adding an optional field with a default value** is always backward compatible
- **Removing a field** is backward compatible but not forward compatible — old consumers that expected the field will receive the default
- **Renaming a field** is a breaking change — use the `aliases` mechanism in Avro to maintain compatibility
- **Changing a field's type** is always breaking and requires a full consumer migration with a deprecation period

## Updating an Existing Schema

Follow the schema evolution process when modifying a registered schema:

1. Identify all consumers of the topic from the schema registry metadata
2. Notify consumer teams of the proposed change and confirm compatibility
3. Register the new schema version after all consumers confirm readiness
4. Coordinate the producer deployment with the consumer migration window
5. Mark the old schema version as deprecated after all consumers have migrated

## Troubleshooting Schema Issues

Common issues and their resolutions:

- **`SerializationException` in consumer logs**: The consumer is receiving a message with a schema ID it cannot find. Check if the producer is using an unregistered schema version or if the registry is unreachable. See [[SOP-052|Handle Schema Compatibility Failure SOP]].
- **Compatibility check fails in CI**: The proposed schema change is breaking. Review the diff and use optional fields with defaults to make the change backward compatible.
- **Schema not found after registration**: Confirm the subject naming convention matches — topics use `{topic-name}-value` as the subject name by convention.

## Next Steps

- Review the Event Schema Registry Standard for all organizational requirements and compatibility mode policies
- Add a schema registry compatibility check step to the CI pipeline for all services that produce Kafka messages
- Familiarize yourself with the [[SOP-059|Update Schema Registry Entry SOP]] for making schema changes safely in production

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
