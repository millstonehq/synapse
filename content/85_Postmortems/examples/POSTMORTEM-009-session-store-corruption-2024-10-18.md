---
id: POSTMORTEM-009
type: postmortem
title: Session Store Corruption 2024-10-18
status: approved
owner: On-Call Engineer
created: '2024-09-27T08:39:09.319Z'
updated: '2026-01-19T05:28:39.255Z'
tags:
  - postmortem
  - user-authentication
summary: Session Store Corruption 2024-10-18
incident_number: INC-170
severity: SEV-3
incident_date: '2026-11-08'
detection_time: '2024-04-16T16:25:19.249Z'
resolution_time: '2026-12-07T06:18:57.579Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-013
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On October 18, 2024, a Redis migration script deployed to production during a maintenance window wrote malformed session records that caused intermittent session validation failures for approximately 15 minutes. Roughly 8% of active sessions were corrupted with a serialization format mismatch, causing those sessions to return deserialization errors on next validation — effectively logging affected users out.

The corruption was detected by a spike in session validation errors and resolved by running a targeted cleanup script that identified and deleted malformed records, allowing affected users to re-authenticate.

## Timeline

- **02:00** - Maintenance window begins. Redis schema migration script runs to add `device_fingerprint` field to session records.
- **02:03** - Migration script completes. 142,000 session records updated.
- **02:05** - First session validation errors appear in logs: `failed to deserialize session: unexpected field type at offset 14`
- **02:08** - `session_validation_error_rate_elevated` alert fires at 3% error threshold.
- **02:11** - On-call identifies deserialization errors are correlated with recently updated session records.
- **02:18** - Root cause confirmed: migration script wrote `device_fingerprint` as JSON string instead of MessagePack binary string, causing format mismatch with the validation path.
- **02:23** - Cleanup script written and tested in staging to identify and delete malformed records.
- **02:28** - Cleanup script run in production. 11,340 malformed records deleted.
- **02:35** - Session validation error rate drops to baseline. Affected users re-authenticate.
- **02:42** - Maintenance window closed. Incident monitoring continues for 30 minutes.
- **03:12** - Incident formally closed.

## Impact

- **Duration**: ~15 minutes of elevated errors (02:08 - 02:35 UTC)
- **Users affected**: ~11,340 users with corrupted session records were effectively logged out
- **Session deletions**: All affected sessions deleted (users required to re-authenticate)
- **SLA impact**: Session validation error rate exceeded 3% briefly; below SEV-2 threshold
- **Customer communications**: No public communication required; affected users received a standard "session expired" re-authentication prompt

## Root Cause Analysis

1. **Migration script used the wrong serialization format**: The Session Management Service uses MessagePack for session record serialization. The migration script was written by a new team member who used Python's `json.dumps()` rather than the `msgpack.packb()` function to write the new `device_fingerprint` field. The resulting records were partially MessagePack (existing fields) and partially JSON (new field), which the validation deserializer rejected.

2. **No format validation in the migration test suite**: The migration test verified that the `device_fingerprint` field was present in updated records but did not verify that the field was correctly serialized in MessagePack format. A format-level assertion would have caught the bug in staging.

## Resolution

1. Identified the subset of session records with the malformed format using a Redis SCAN with a deserialization probe
2. Deleted all malformed records (affected users prompted to re-authenticate on next request)
3. Confirmed no new malformed records being created (the runtime path uses the correct serializer)

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add serialization format assertion to migration test suite | Session team | P1 | 2024-10-25 | Completed |
| Add migration script review checklist that includes serialization format verification | Engineering manager | P2 | 2024-11-01 | Completed |
| Add session record format validation on read (reject and delete malformed records instead of erroring) | Session team | P2 | 2024-11-15 | In progress |
| Document MessagePack serialization requirement in session service contributing guide | Session team | P3 | 2024-11-15 | Pending |

## Lessons Learned

- **What went well**: Alerting fired within 3 minutes of the first errors. Root cause was identified quickly because error messages included the deserialization offset, pointing directly to the malformed field.
- **What went poorly**: The migration test only checked presence, not format, of the new field. A single-line format assertion would have prevented the incident.
- **What was lucky**: The corrupted records were identifiable and deletable without data loss. Session deletion means users are re-authenticated, which is the expected behavior for an expired or invalid session.
