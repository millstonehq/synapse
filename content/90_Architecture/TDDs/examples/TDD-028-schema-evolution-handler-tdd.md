---
id: TDD-028
type: tdd
title: Schema Evolution Handler TDD
status: review
owner: Principal Engineer
created: '2025-11-06T15:27:11.498Z'
updated: '2025-09-28T01:07:45.903Z'
tags:
  - tdd
  - data-pipeline
summary: Schema Evolution Handler TDD
related_adrs:
  - ADR-0025
  - ADR-0022
example: true
---

## Summary

Design the Schema Evolution Handler — a Node.js Lambda service that mediates schema registration and compatibility validation requests for the Schema Registry Service. The handler enforces Avro compatibility rules (BACKWARD, FORWARD, FULL) on new schema submissions, translates incompatible changes into a structured rejection response with guidance on remediation, and propagates approved schema versions to the DynamoDB schema store.

This TDD implements the Schema Registry with Avro decision from [[ADR-0025|ADR-0025: Implement Schema Registry with Avro]] and incorporates event streaming patterns from [[ADR-0022|ADR-0022]].

## Overview

The Schema Evolution Handler is a stateless Node.js Lambda that sits between schema producers and the DynamoDB schema store. On each schema registration request, it fetches the latest registered schema version for the subject, invokes the Avro compatibility checker against the proposed schema, and either stores the new version transactionally or returns a structured rejection error. The handler exposes a Confluent Schema Registry-compatible REST API so standard Confluent clients require no modification.

Key design principles:
- **Compatibility-first**: Every registration attempt is compatibility-checked before storage; no schema reaches DynamoDB without passing the configured compatibility mode
- **Transactional writes**: DynamoDB `TransactWriteItems` ensures atomicity of schema content and metadata writes
- **Detailed rejections**: Compatibility failures return structured error responses identifying the specific incompatible field and the compatibility rule violated
- **Caching**: Subject compatibility configurations and latest schema versions are cached in Lambda memory with 5-minute TTL to reduce DynamoDB read load

## Architecture

### Component Diagram

The handler has four modules:

- **API Layer**: Parses Confluent Schema Registry REST requests; routes to registration or compatibility-check handlers
- **Compatibility Checker**: Fetches latest schema version from cache or DynamoDB; invokes Avro schema compatibility library; returns pass/fail with field-level detail
- **Schema Store**: Executes DynamoDB `TransactWriteItems` for atomic metadata + content writes; manages schema ID allocation via atomic counter
- **Cache Layer**: In-memory LRU cache for subject configs and latest schema versions; reduces DynamoDB reads on high-registration-volume bursts

### Compatibility Modes

- **`BACKWARD`**: Add optional fields with defaults; delete optional fields
- **`FORWARD`**: Delete fields; add required fields with defaults
- **`FULL`**: Only add optional fields with defaults
- **`NONE`**: No compatibility check; all changes accepted

## Information Model

### Core Entities

- **SchemaVersion**: Stored in DynamoDB. Fields: `subject`, `version`, `schema_id`, `schema_content` (JSON string of Avro schema), `compatibility_mode`, `created_at`
- **SubjectConfig**: Stored in DynamoDB. Fields: `subject`, `compatibility_mode`, `updated_at`
- **CompatibilityResult**: Internal. Fields: `compatible`, `violations` (array of `{field, rule, message}`)

### DynamoDB Tables

- `schemas` table: partition key `subject`, sort key `version`; GSI on `schema_id` for ID-to-schema lookups; `TransactWriteItems` used for all writes
- `subject_configs` table: partition key `subject`; stores per-subject compatibility mode overrides

## Interfaces

### Confluent-Compatible REST Endpoints

- `POST /subjects/{subject}/versions` — Register a new schema version (compatibility check + write)
- `GET /subjects/{subject}/versions/latest` — Retrieve latest schema version for a subject
- `GET /schemas/ids/{id}` — Retrieve schema by global schema ID
- `POST /compatibility/subjects/{subject}/versions/latest` — Test compatibility without registering
- `PUT /config/{subject}` — Set per-subject compatibility mode

### Internal Compatibility Checker Interface

```typescript
interface CompatibilityResult {
  compatible: boolean;
  violations: Array<{
    field: string;
    rule: string;
    message: string;
  }>;
}

async function checkCompatibility(
  proposed: AvroSchema,
  existing: AvroSchema,
  mode: CompatibilityMode
): Promise<CompatibilityResult>
```

## Files and Layout

```
src/
  handler.ts                      - Lambda entry point, request routing
  api/
    register.ts                   - POST /subjects/{subject}/versions handler
    retrieve.ts                   - GET endpoints for schema retrieval
    compatibility.ts              - POST /compatibility handler
    config.ts                     - PUT /config handler
  compatibility/
    checker.ts                    - Avro compatibility evaluation logic
    rules/
      backward.ts                 - BACKWARD mode rules
      forward.ts                  - FORWARD mode rules
      full.ts                     - FULL mode rules
  store/
    schema-store.ts               - DynamoDB TransactWriteItems writes
    id-allocator.ts               - Atomic schema ID counter
  cache/
    subject-cache.ts              - In-memory LRU cache for subjects/configs
  models/
    schema-version.ts
    subject-config.ts
    compatibility-result.ts
```

## Work Plan

1. **Phase 1 — Core Registration (Week 1-2)**: DynamoDB write/read, schema ID allocation, basic BACKWARD compatibility check
2. **Phase 2 — Full Compatibility Modes (Week 3)**: FORWARD and FULL mode rules, structured violation responses
3. **Phase 3 — Caching Layer (Week 4)**: LRU cache for subject configs and latest versions, cache invalidation on writes
4. **Phase 4 — Confluent API Compatibility (Week 5)**: Full REST endpoint parity with Confluent Schema Registry v7; client library integration tests
5. **Phase 5 — Resilience Testing (Week 6)**: Lambda timeout scenarios, DynamoDB transact failure handling, burst registration load tests

## Risks and Mitigations

- **Risk**: DynamoDB `TransactWriteItems` failures during Lambda timeout leave no partial state. **Mitigation**: Transactions are atomic; a timed-out Lambda means no write committed; the Schema Registry Corruption incident (Feb 2025) drove this requirement.
- **Risk**: Schema ID counter collisions under concurrent Lambda instances. **Mitigation**: ID allocation uses DynamoDB conditional writes with atomic increment; concurrent allocations serialize at DynamoDB level.
- **Risk**: Cache serving stale schemas after compatibility mode change. **Mitigation**: Config writes invalidate subject cache entry immediately; 5-minute TTL limits maximum staleness for reads.
- **Risk**: Avro compatibility library bugs cause incorrect approvals. **Mitigation**: Compatibility checker is unit-tested against the full Avro spec compatibility matrix; suspicious approvals trigger a compatibility audit alert.

## Operations

- **Deployment**: Lambda deployed via Terraform; new versions deployed via alias promotion (no traffic cutover risk).
- **Monitoring**: CloudWatch metrics for registration rate, compatibility rejection rate, cache hit rate, DynamoDB write latency.
- **Alerting**: Alert on compatibility rejection rate > 20% (indicates a producer deploying schema changes without coordination), DynamoDB write error rate > 0.1%.
- **Rollback**: Lambda alias rollback to previous version in under 60 seconds; DynamoDB schema table supports PITR for data recovery.
