---
id: ADR-0025
type: adr
title: Implement Schema Registry with Avro
status: approved
owner: Staff Engineer
created: '2024-12-12T09:24:48.749Z'
updated: '2025-09-08T18:14:10.365Z'
tags:
  - adr
  - data-pipeline
summary: Implement Schema Registry with Avro
example: true
---

## Context

The Kafka-based event streaming platform was operating with JSON-encoded messages on all topics. This created several problems as the platform matured:

- **No schema enforcement**: Producers could publish malformed or structurally incompatible messages; consumers discovered breakage only at deserialization time
- **Undiscoverable contracts**: Consumer teams had no authoritative source for topic message structures; contracts were communicated informally via Slack or Confluence pages that drifted from reality
- **Schema drift incidents**: Two production incidents in 2024 were caused by producers adding required fields without coordinating with consumers
- **Storage inefficiency**: JSON's verbosity created approximately 3–5x the storage and bandwidth overhead compared to binary formats for high-volume topics

Requirements for the schema registry solution:
- Centralized, versioned schema storage accessible to all producers and consumers
- Schema compatibility enforcement (prevent breaking changes from being published)
- Client libraries available for Java (primary), Python, and Node.js
- Self-hostable or API-compatible with Confluent Schema Registry wire protocol

## Decision

Implement a **custom Schema Registry Service using Apache Avro** as the serialization format, with DynamoDB as the schema store and Lambda as the API layer.

The registry exposes a Confluent Schema Registry-compatible REST API, allowing use of standard Confluent Avro SerDe clients in Java and Python producers and consumers without custom client code. Schemas are stored in DynamoDB with `transactWriteItems` for atomic multi-attribute writes. Compatibility mode is set to `BACKWARD` by default for all subjects; `FULL` compatibility is required for topics consumed by the data lake ingestion tier. Schema IDs are encoded in the first 5 bytes of each Avro message (magic byte + 4-byte schema ID) per Confluent wire format.

## Consequences

**Positive:**
- Confluent wire protocol compatibility means standard Avro SerDe clients work without modification
- BACKWARD compatibility enforcement prevents consumer breakage from producer schema changes
- Binary Avro encoding reduces payload size by ~70% vs. JSON for typical event messages
- DynamoDB PITR provides schema backup and point-in-time restore capability (demonstrated in Feb 2025 incident recovery)
- Schema IDs in message bytes allow consumers to resolve schema without topic metadata

**Negative:**
- Custom registry implementation requires ongoing maintenance vs. using Confluent Cloud or a managed registry
- Avro's schema evolution rules (no field type changes, only additions with defaults) require producer discipline
- DynamoDB per-request pricing scales with registration volume during high-burst registration events
- Debugging Avro deserialization errors is harder than JSON — binary format is not human-readable in raw logs

**Neutral:**
- Protobuf was evaluated as an alternative serialization format; Avro was chosen for stronger Confluent ecosystem alignment
- The registry is stateless at the Lambda layer; horizontal scaling is automatic

## Alternatives Considered

**Confluent Schema Registry (self-hosted):**
- Pro: Reference implementation, Confluent wire protocol native, full feature set, wide client library support
- Con: Requires running a Zookeeper-backed JVM service; adds operational complexity; Confluent's licensing for advanced features (subject-level compatibility) requires commercial license
- Rejected because: The operational footprint of a persistent JVM service with Zookeeper dependency was disproportionate to registry traffic volume; the Lambda-based custom service achieves equivalent functionality at lower operational cost

**AWS Glue Schema Registry:**
- Pro: Fully managed, native AWS integration, no operational overhead, supports Avro and JSON Schema
- Con: Not Confluent wire protocol compatible — would require custom SerDe in all producers and consumers; limited compatibility mode options at time of evaluation
- Rejected because: Confluent wire protocol compatibility was required to use standard Kafka client libraries without modification

**JSON Schema with inline validation:**
- Pro: No serialization format change required, human-readable messages, broad tooling
- Con: No centralized schema enforcement — validation would be per-client opt-in; no storage efficiency gain; schema drift problem not fully solved
- Rejected because: Storage and schema enforcement requirements cannot be met with JSON Schema validation alone
