---
id: RUNBOOK-012
type: runbook
title: OAuth Token Store Capacity Runbook
status: draft
owner: On-Call Engineer
created: '2024-07-14T20:43:59.281Z'
updated: '2025-06-16T17:07:00.080Z'
tags:
  - runbook
  - user-authentication
summary: OAuth Token Store Capacity Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / Redis 7 / DynamoDB

## Alerts

- `oauth_token_store_memory_high` - Redis token store memory utilization exceeds 80% of `maxmemory`
- `oauth_token_store_eviction_rate_high` - Redis is evicting more than 100 keys per minute from the token store
- `oauth_refresh_token_count_spike` - Active refresh token count exceeds 1.5x the rolling 7-day average
- `oauth_token_store_connection_errors` - Token store connection errors exceed 0.5% of token operations

## Diagnosis Steps

1. **Check Redis memory utilization** - Run `redis-cli -h oauth-token-store info memory` and review `used_memory_human`, `maxmemory_human`, and `mem_fragmentation_ratio`. If fragmentation ratio is above 1.5, fragmentation is a contributing factor.
2. **Check eviction policy and evicted keys** - Run `redis-cli -h oauth-token-store info stats | grep evicted_keys`. If evictions are occurring, check whether the `maxmemory-policy` is `noeviction` (tokens are failing to write) or `allkeys-lru` (older tokens are being evicted, causing validation failures).
3. **Check for a refresh token leak** - Query the token count: `redis-cli -h oauth-token-store dbsize`. If the count is growing rapidly, there may be a refresh token rotation bug creating tokens without expiring old ones. Check recent deployments to the authentication service.
4. **Check for expired token accumulation** - If Redis is not configured with TTLs on token keys, expired tokens may be accumulating. Sample 10 token keys and verify each has a TTL set: `redis-cli -h oauth-token-store TTL <token-key>`.
5. **Check token store cluster health** - Verify all Redis nodes are in the cluster: `redis-cli -h oauth-token-store cluster nodes`. If a node is down, memory is unevenly distributed across remaining nodes.

## Remediation Steps

1. **If memory is above 85% and evictions are occurring**: Scale the Redis cluster to add a new node immediately via the infrastructure team. This is the preferred long-term fix; do not solely rely on eviction policy changes.
2. **If expired tokens are accumulating without TTLs**: Run a targeted cleanup scan to identify and delete expired token keys. Deploy a hotfix to the authentication service to ensure new tokens are issued with appropriate TTL values.
3. **If a refresh token leak is suspected from a recent deploy**: Roll back the authentication service to the previous version immediately to stop the leak, then investigate the root cause.
4. **If fragmentation is high**: Schedule a Redis memory defragmentation during a low-traffic window: `redis-cli -h oauth-token-store memory purge`. Monitor memory utilization before and after.
5. **If connection errors are occurring**: Check network connectivity between authentication service pods and the Redis cluster. Restart the Redis connection pool in the auth service by rolling pods: `kubectl rollout restart deployment/auth-service -n auth`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks Redis memory and eviction stats |
| 10 min | Post diagnosis in #auth-incidents; page infrastructure on-call if Redis scaling is needed |
| 20 min | If token evictions are causing login failures: page Platform Lead immediately |
| 30 min | If not resolved: notify Engineering Manager; assess token validation failure impact |
| 60 min | Escalate to Director of Engineering if persistent login failures are affecting users |

## Dashboards

- [OAuth Token Store](https://grafana.example.com/d/oauth-token-store) - Redis memory, eviction rate, key count, connection pool
- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - Token issuance and refresh rates, validation error rates
- [Redis Cluster Health](https://grafana.example.com/d/redis-cluster) - Node status, replication lag, slot distribution
