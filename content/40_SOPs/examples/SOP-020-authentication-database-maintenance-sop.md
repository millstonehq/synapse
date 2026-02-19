---
id: SOP-020
type: sop
title: Authentication Database Maintenance SOP
status: draft
owner: DevOps Lead
created: '2024-10-29T15:12:24.790Z'
updated: '2025-12-09T13:06:57.342Z'
tags:
  - sop
  - user-authentication
summary: Authentication Database Maintenance SOP
related_process: PROCESS-010
related_systems:
  - SYSTEM-007
example: true
---

## Preconditions

- A maintenance window has been scheduled and approved by the Platform Lead during off-peak hours
- A full database backup has been completed and verified within the last 4 hours
- The on-call engineer is available to monitor authentication health during the maintenance window
- An approved change ticket exists for the maintenance operation
- Users have been notified if the maintenance may cause brief authentication degradation

## Materials/Access

- Database admin credentials for the authentication database (from secrets manager)
- Access to the database administration console (pgAdmin, psql, or equivalent)
- Access to the authentication service monitoring dashboard
- Database backup verification script: `./scripts/verify-auth-db-backup.sh`
- Change ticket ID

## Procedure

1. Verify the recent database backup is valid by running `./scripts/verify-auth-db-backup.sh` and confirming it completes without errors.
2. Announce the maintenance window in #auth-deployments: "Starting auth DB maintenance @ [time] for [CHANGE-TICKET]. On-call: [name]."
3. Enable the authentication service's read-only mode if the maintenance operation requires exclusive write access (configuration flag: `AUTH_DB_READONLY=true`).
4. Connect to the authentication database using the admin credentials and execute the planned maintenance operations (vacuuming, index rebuilding, schema migrations, or cleanup of expired token records).
5. For expired session cleanup, execute: `DELETE FROM sessions WHERE expires_at < NOW() - INTERVAL '7 days';` and verify the row count matches expectations before committing.
6. After all maintenance operations are complete, disable read-only mode and confirm the authentication service resumes normal write operations.
7. Run the authentication smoke test suite to confirm database connectivity and login flows are functioning: `./scripts/auth-smoke-test.sh --env production`.
8. Monitor authentication error rate and database connection pool metrics for 15 minutes after maintenance completes.
9. Post in #auth-deployments confirming maintenance completion and metrics status, then close the change ticket.

## Validation

- Authentication smoke tests pass after maintenance completes
- Database connection pool shows healthy utilization (below 60% of pool max)
- No authentication errors spike in the 15 minutes post-maintenance
- Database disk usage reflects expected reduction after cleanup operations

## Rollback

1. If a schema migration fails mid-execution, roll back the transaction immediately using the prepared rollback SQL script from the change ticket.
2. If the authentication service fails to reconnect after maintenance, verify the database is accepting connections from the service's IP range and restart the connection pool by rolling the auth service pods.
3. If data loss is suspected, immediately stop write operations (set `AUTH_DB_READONLY=true`), escalate to the Platform Lead, and initiate database restoration from backup.
4. Document all rollback actions in the change ticket with timestamps and the rollback reason.
