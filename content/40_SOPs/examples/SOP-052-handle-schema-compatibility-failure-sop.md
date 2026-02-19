---
id: SOP-052
type: sop
title: Handle Schema Compatibility Failure SOP
status: review
owner: SRE Lead
created: '2024-07-28T19:08:58.407Z'
updated: '2025-05-04T13:32:56.241Z'
tags:
  - sop
  - data-pipeline
summary: Handle Schema Compatibility Failure SOP
related_process: PROCESS-066
related_systems:
  - SYSTEM-026
example: true
---

## Preconditions

- A schema compatibility failure has been identified: either a CI compatibility check failure or a runtime consumer deserialization error
- The affected topic name and schema subject are known
- The producer and consumer versions involved in the conflict are identified
- You have write access to the schema registry (Schema Registry Admin role)

## Materials/Access

- Schema Registry web UI or `kafka-avro-console` CLI access
- Access to the Kafka consumer error log stream or Grafana deserialization error dashboard
- Access to the #data-incidents Slack channel
- The current and proposed schema definitions (JSON or Avro IDL files)

## Procedure

1. Confirm the nature of the failure: run `GET /subjects/{subject}/versions/latest` against the schema registry API to retrieve the current registered schema.
2. Compare the current schema with the proposed schema to identify the breaking change (removed field, type change, or required field addition).
3. Post in #data-incidents: "Schema compatibility failure on subject [subject]. Investigating. Producer: [service]. Consumer lag: [value]."
4. If the failure is in CI, block the producer deployment; do not proceed until schema is fixed or consumers are migrated.
5. If the failure is in production (live consumer deserialization errors), pause the affected consumer group to prevent further error accumulation.
6. Work with the schema owner to produce a compatible schema version: add new fields as optional with defaults, never remove required fields directly.
7. Register the corrected schema version via `POST /subjects/{subject}/versions` and confirm the registry returns a new schema ID.
8. Deploy the updated producer using the new schema ID and confirm messages are serialized correctly.
9. Restart the paused consumer group and verify deserialization errors drop to zero in Grafana.

## Validation

- Schema registry returns compatibility check status "COMPATIBLE" for the new schema version
- Consumer group error rate for the affected topic returns to 0 within 5 minutes of consumer restart
- Consumer lag is decreasing and consumer is processing messages at the expected throughput
- No new `SerializationException` entries appear in consumer logs

## Rollback

1. If the corrected schema still causes failures, delete the newly registered schema version from the registry.
2. Revert the producer to the previous schema version by deploying the prior producer image.
3. Restart the consumer group against the previous known-good schema version.
4. Confirm consumer processing resumes and error rate returns to zero before investigating further.
5. Open a schema evolution ticket to plan a proper migration with a deprecation period.
