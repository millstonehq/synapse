---
id: FLOW-023
type: flow
title: Schema Validation Flow
status: proposed
owner: QA Engineer
created: '2024-10-05T21:00:58.812Z'
updated: '2025-06-06T10:59:38.494Z'
tags:
  - flow
  - data-pipeline
summary: Schema Validation Flow
feature_area: Data Pipeline
related_prds:
  - PRD-030
example: true
---

## Steps

### Step 1: Producer Requests Schema Registration

A new or updated upstream service deploys with a changed Avro schema. As part of the service's startup or CI/CD deploy process, it calls `POST /subjects/{subject}/versions` on the Schema Registry Service API with the proposed Avro schema JSON. The request includes the subject name (e.g., `orders-events-v2-value`) and the schema content.

### Step 2: Schema Registry Fetches Existing Schema for Subject

The Schema Evolution Handler Lambda looks up the latest registered schema version for the subject. If no existing schema is found for the subject, the proposed schema is treated as v1 and compatibility check is skipped (all initial schemas are accepted). If an existing schema is found, the handler fetches it from the DynamoDB schema store (or cache) for comparison.

### Step 3: Compatibility Check Runs

The compatibility checker evaluates the proposed schema against the existing latest version using the configured compatibility mode for the subject (default: BACKWARD). The checker applies field-level rules:
- **BACKWARD** (default): new schema can read messages written with old schema. Allowed: add optional fields with defaults. Rejected: removing required fields, changing field types.
- If the compatibility mode is FULL, both BACKWARD and FORWARD rules are applied simultaneously.

If compatibility passes, execution continues to Step 4. If compatibility fails, the handler returns a 409 Conflict response with a structured rejection body listing each incompatible field, the rule violated, and suggested remediation.

### Step 4: Schema Written to DynamoDB Transactionally

On compatibility pass, the Schema Evolution Handler executes a DynamoDB `TransactWriteItems` call that atomically writes both the schema metadata item (subject, version, schema_id, compatibility_mode, created_at) and the schema content item (schema_id, avro_schema_json) in a single transaction. The schema ID is allocated via an atomic DynamoDB counter increment. If the transaction fails (timeout, conditional check failure), no partial write is committed and the handler returns a 500 error.

### Step 5: Producer Receives Schema ID and Begins Publishing

On successful registration, the Schema Registry API returns a `{"id": <schema_id>}` response. The producer's Avro serializer caches the schema ID and uses it to encode the 5-byte message prefix (magic byte + schema ID) on all subsequent messages to the topic. Consumers receiving messages with this schema ID can retrieve the schema from the registry to deserialize.

## Expected Results

- Compatible schema changes are registered atomically and the new schema ID is immediately available to producers
- Incompatible schema changes are rejected with a structured error response identifying the specific incompatibility before any message is published with the new schema
- No partial schema writes reach the DynamoDB schema store under any failure condition (timeout, crash)
- Rejected schemas are logged with the full rejection detail for producer team debugging
- Accepted schemas are available to consumers via the `GET /schemas/ids/{id}` endpoint within 1 second of registration

## User Info

| Field | Value |
|-------|-------|
| Role | Producer service / data engineer deploying a schema change |
| Permissions | Write access to Schema Registry API (authenticated via service IAM role or API key) |
| Test subject | `orders-events-test-v2-value` (staging environment) |
| Test schema | `avro/orders-events-v2.avsc` in the upstream service repository |
| Environment | Staging |
