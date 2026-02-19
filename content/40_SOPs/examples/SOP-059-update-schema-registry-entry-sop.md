---
id: SOP-059
type: sop
title: Update Schema Registry Entry SOP
status: approved
owner: SRE Lead
created: '2024-02-16T16:50:13.634Z'
updated: '2025-07-23T01:48:36.203Z'
tags:
  - sop
  - data-pipeline
summary: Update Schema Registry Entry SOP
related_process: PROCESS-033
related_systems:
  - SYSTEM-028
example: true
---

## Preconditions

- A schema change has been approved through the schema evolution process with consumer sign-off
- The new schema definition (Avro, Protobuf, or JSON Schema) is finalized and reviewed
- A compatibility check has been run and confirmed the new version is compatible with the configured compatibility mode
- The schema registry admin credentials are available in Vault

## Materials/Access

- Schema Registry REST API access or Confluent Control Center UI access
- Schema definition files in the pipeline code repository
- Access to #data-schema-changes Slack channel

## Procedure

1. Retrieve the current schema for the subject: `GET /subjects/{subject}/versions/latest` and confirm you are targeting the correct subject.
2. Run the compatibility check against the proposed schema: `POST /compatibility/subjects/{subject}/versions/latest` with the new schema body; confirm the response is `{"is_compatible": true}`.
3. Post in #data-schema-changes: "Registering new schema version for [subject]. Change: [brief description]. Approved by: [approver]."
4. Register the new schema version: `POST /subjects/{subject}/versions` with the new schema definition in the request body.
5. Note the returned schema ID; record it in the schema change ticket.
6. Verify the new version is visible: `GET /subjects/{subject}/versions` should list the new version number.
7. Update the schema metadata in the data catalog entry for any dataset affected by this schema change.
8. Notify consumer teams via #data-schema-changes with the new schema ID and the effective date for migration.

## Validation

- The schema registry returns the new schema version when queried for the subject
- The compatibility endpoint confirms the new version as compatible when tested against the previous version
- The schema ID is recorded in the change ticket and data catalog entry
- Consumer teams have acknowledged the schema update notification

## Rollback

1. If the registered schema causes production issues, delete the new schema version: `DELETE /subjects/{subject}/versions/{version}`.
2. Confirm the deleted version is no longer returned by the registry for the subject.
3. Notify consumer teams that the schema version has been rolled back.
4. Revert any producer deployments that were using the new schema ID.
5. Document the rollback in the schema change ticket and schedule a revised migration plan.
