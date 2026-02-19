---
id: SOP-009
type: sop
title: Payment Database Failover SOP
status: approved
owner: DevOps Lead
created: '2025-12-01T21:30:40.371Z'
updated: '2026-06-06T08:53:01.204Z'
tags:
  - sop
  - payment-processing
summary: Payment Database Failover SOP
related_process: PROCESS-006
related_systems:
  - SYSTEM-005
example: true
---

## Preconditions

- The primary payment database is confirmed as unhealthy: either unresponsive, showing replication errors, or with data corruption suspected
- The standby replica is confirmed to be in sync (replication lag < 30 seconds at time of failure) or the last known good state has been assessed
- Engineering Manager or Director of Engineering has authorized the failover
- The payment service has been confirmed as the primary consumer of the database being failed over
- The on-call DBA and payments on-call engineer are both available for the failover window

## Materials/Access

- Access to the database management console (AWS RDS console, Aurora console, or equivalent)
- Access to the payment service deployment dashboard to manage connection string updates
- Access to the monitoring dashboard to confirm replica health and replication lag
- Database admin credentials stored in secrets management system
- #payment-incidents Slack channel for real-time coordination

## Procedure

1. Post in #payment-incidents: "Initiating payment database failover. Primary: [db-primary]. Replica: [db-replica]. Authorized by: [name]."
2. Confirm replica replication lag is acceptable: check CloudWatch or equivalent for `ReplicaLag` metric; lag > 30 seconds requires DBA assessment before proceeding.
3. Put the payment service into read-only mode using the feature flag console to prevent new writes during failover.
4. Initiate the failover in the database management console: select the primary instance and click "Failover" (for Aurora/RDS Multi-AZ) or promote the replica manually.
5. Monitor the failover progress; typical completion time is 30-60 seconds for Multi-AZ and 1-5 minutes for manual promotion.
6. Confirm the new primary endpoint is resolving correctly by testing a connection from the database management console.
7. Update the payment service database connection string if the endpoint has changed (in secrets manager or config map); trigger a rolling restart if required.
8. Disable read-only mode in the feature flag console to resume payment processing.
9. Monitor payment success rate and database connection metrics for 15 minutes post-failover.
10. Post in #payment-incidents: "Payment database failover complete. New primary: [endpoint]. Success rate: X%."

## Validation

- Payment service is processing transactions successfully against the new primary database
- Database connection pool shows healthy connections with no `connection refused` errors in service logs
- Payment success rate has returned to pre-incident baseline within 5 minutes of failover completion
- Read-only mode has been fully disabled and no payments are being rejected for read-only reasons
- Replication has resumed from the new primary to a new standby replica

## Rollback

1. If the failover results in data inconsistency or the new primary is also unhealthy, post in #payment-incidents immediately.
2. Enable read-only mode to stop all writes while the situation is assessed.
3. Contact the on-call DBA to assess the data state on both the original primary (if recoverable) and the new primary.
4. Do not attempt to fail back without explicit DBA confirmation that data consistency has been verified.
5. If payment processing cannot be safely restored within 30 minutes, escalate to Director of Engineering and initiate the payment freeze SOP.
