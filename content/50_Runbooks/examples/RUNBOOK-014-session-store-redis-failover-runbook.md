---
id: RUNBOOK-014
type: runbook
title: Session Store Redis Failover Runbook
status: review
owner: On-Call Engineer
created: '2024-01-23T04:41:46.284Z'
updated: '2026-05-10T16:23:22.638Z'
tags:
  - runbook
  - user-authentication
summary: Session Store Redis Failover Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / Redis 7 Cluster / DynamoDB

## Alerts

- `session_store_connection_errors` - Session store connection errors exceed 1% for 2 minutes
- `session_store_primary_down` - Redis primary node health check failing for 30 seconds
- `session_store_replica_lag_high` - Replica replication lag exceeds 10 seconds
- `session_store_memory_critical` - Session store memory utilization exceeds 90% of `maxmemory`

## Diagnosis Steps

1. **Check Redis cluster node status** - Run `redis-cli -h session-store cluster nodes` to see the current state of all nodes. Identify which node is primary and which are replicas, and confirm each node's health state (connected, disconnected, fail).
2. **Check automatic failover status** - Redis Sentinel or Redis Cluster should automatically promote a replica when the primary fails. Check whether a failover has already been initiated: `redis-cli -h session-store sentinel master auth-session`.
3. **Check authentication service session operation errors** - In Kibana, filter for `service:auth` and `operation:session_store` to see whether session reads, writes, or deletes are failing. Identify whether failures are total (node down) or partial (replica lag).
4. **Check session store memory pressure** - If the memory alert fired in conjunction with connection errors, memory exhaustion may be causing the primary to become unresponsive. Run `redis-cli -h session-store info memory`.
5. **Verify network connectivity** - From an authentication service pod, test reachability: `redis-cli -h session-store ping`. If timeout occurs, there may be a network policy or security group issue.

## Remediation Steps

1. **If automatic failover has been initiated by Sentinel/Cluster**: Wait for failover to complete (usually 30–60 seconds). Update the authentication service connection string if it is not using a Sentinel-aware Redis client. Restart auth service pods to pick up the new primary address.
2. **If automatic failover has not triggered**: Manually trigger failover via Redis Sentinel: `redis-cli -h sentinel-host sentinel failover auth-session`. Confirm the new primary is accepting writes before restarting auth service pods.
3. **If all Redis nodes are unreachable**: Enable the authentication service's graceful degradation mode (`AUTH_SESSION_STORE_FALLBACK=database`) which uses the database as a temporary session store at reduced performance. Page the infrastructure on-call immediately for Redis cluster recovery.
4. **If memory is causing primary unresponsiveness**: Connect to a healthy replica and run `DEBUG SLEEP 0` on the primary if reachable to unblock it. If unreachable, proceed with manual failover (Remediation Step 2).
5. **If replica lag is causing stale session reads**: Temporarily configure the authentication service to read sessions exclusively from the primary by setting `AUTH_SESSION_READ_PRIMARY=true`. This increases primary load but ensures consistency.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks Redis cluster node status |
| 5 min | Post initial status in #auth-incidents; page infrastructure on-call if Redis recovery is needed |
| 15 min | If all sessions are invalid (users logged out): notify Engineering Manager and prepare user communication |
| 30 min | If not resolved: page Platform Lead; escalate to major incident if user impact is confirmed |
| 60 min | Escalate to Director of Engineering; activate major incident protocol if session store is not recovered |

## Dashboards

- [Session Store Health](https://grafana.example.com/d/session-store) - Redis primary/replica status, memory, connection count, latency
- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - Session operation error rates, login success rates
- [Redis Cluster](https://grafana.example.com/d/redis-cluster) - Node health, replication lag, slot distribution, failover history
