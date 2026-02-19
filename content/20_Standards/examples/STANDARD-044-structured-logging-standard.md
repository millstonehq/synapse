---
id: STANDARD-044
type: standard
title: Structured Logging Standard
status: approved
owner: Head of Engineering
created: '2024-05-05T00:49:13.709Z'
updated: '2026-09-22T11:43:41.177Z'
tags:
  - standard
  - monitoring-stack
summary: Structured Logging Standard
related_policies:
  - POLICY-036
  - POLICY-039
example: true
related_systems:
  - SYSTEM-037
  - SYSTEM-036
---

## Area

This standard defines the required format and mandatory fields for all application logs emitted by production services. Structured logs enable centralized aggregation, search, and alerting via the log ingestion pipeline. Ad-hoc or unstructured log output is not permitted in production services.

All engineering teams are required to implement this standard when building or operating production services. The standard applies to application logs; kernel and system logs are managed separately by the platform team.

## Controls

- All log entries must be emitted as single-line JSON objects to stdout or stderr
- Every log entry must include these mandatory fields: `timestamp` (ISO 8601), `level` (one of: DEBUG, INFO, WARN, ERROR, FATAL), `service`, `trace_id`, `message`
- Log levels must be set to INFO in production by default; DEBUG logging in production requires an incident or explicit platform team authorization
- Log entries must not contain PII, credentials, tokens, or payment card data; services must redact or mask sensitive fields before logging
- `trace_id` and `span_id` fields must be populated from the active trace context when the service uses distributed tracing
- Logs at ERROR or FATAL level must include an `error` field with the error message and `stack_trace` where available
- Log volume must not exceed 1 MB per second per service pod without platform team approval; services must use sampling for high-frequency debug events

## Compliance Mappings

- SOC 2: CC7.2 (System Monitoring) — structured logs provide the audit trail required for anomaly detection
- NIST SP 800-92 (Log Management Guide) — mandatory fields and retention align with NIST guidance
- Internal: [[POLICY-036|Monitoring Data Retention Policy]], [[POLICY-039|Observability Standards Policy]]

## Related Policies

- [[POLICY-036|Monitoring Data Retention Policy]]
- [[POLICY-039|Observability Standards Policy]]
