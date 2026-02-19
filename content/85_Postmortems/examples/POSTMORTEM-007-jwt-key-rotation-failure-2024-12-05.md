---
id: POSTMORTEM-007
type: postmortem
title: JWT Key Rotation Failure 2024-12-05
status: draft
owner: On-Call Engineer
created: '2024-10-29T17:43:11.092Z'
updated: '2026-09-13T00:14:02.967Z'
tags:
  - postmortem
  - user-authentication
summary: JWT Key Rotation Failure 2024-12-05
incident_number: INC-168
severity: SEV-3
incident_date: '2026-02-21'
detection_time: '2024-08-17T00:14:15.442Z'
resolution_time: '2024-01-29T12:54:08.451Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-019
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On December 5, 2024, a quarterly JWT signing key rotation caused a 4-hour window of elevated token validation failures across resource servers. The rotation completed successfully on the OAuth Authorization Server side, but resource servers with aggressive JWKS caching did not pick up the new public key in time. Approximately 3.2% of API calls were rejected with 401 Unauthorized errors during the peak impact window.

The incident was caused by a combination of a too-short JWKS cache TTL overlap period (7 days, but some resource servers had 24-hour cache TTLs) and an absence of coordination between the key rotation runbook and the resource server cache configuration. The incident was resolved by forcing a JWKS cache flush across all resource servers.

## Timeline

- **09:00** - Scheduled quarterly JWT key rotation begins. New RS256 key pair generated in Vault.
- **09:05** - New public key added to JWKS endpoint alongside old key. New tokens now signed with new key.
- **09:07** - Old key removed from signing (tokens no longer issued with old key), but old key retained in JWKS for validation of existing tokens.
- **09:12** - First reports of 401 errors from API Gateway logs. Error rate at 0.4%.
- **09:18** - `api_gateway_auth_error_rate_elevated` alert fires at 1% error rate threshold.
- **09:25** - On-call identifies that resource servers are rejecting tokens signed with the new key.
- **09:40** - Root cause confirmed: resource servers have 24-hour JWKS cache TTLs; new public key not yet cached.
- **10:00** - JWKS cache flush initiated on API Gateway. Error rate drops immediately for API Gateway traffic.
- **10:15** - JWKS cache flush initiated on microservices with cached JWKS. Each service requires individual restart.
- **12:45** - All services confirmed to have the new JWKS. Error rate returns to baseline.
- **13:00** - Incident closed.

## Impact

- **Duration**: ~4 hours (09:07 - 13:00 UTC)
- **Users affected**: Users making API calls via services with stale JWKS caches; new logins were unaffected
- **Error volume**: Approximately 18,000 API calls rejected with 401 errors during the impact window
- **SLA impact**: 3.2% peak API error rate, exceeding the 0.1% SLO for affected services
- **Customer communications**: Status page updated at 09:30 with advisory for developers experiencing 401 errors

## Root Cause Analysis

1. **JWKS cache TTL exceeded the key overlap period for some services**: The key rotation runbook specified a 7-day overlap period (old key retained in JWKS for 7 days after rotation). However, several microservices had JWKS cache TTLs of 24 hours, which is within the overlap window in theory — but the rotation happened to occur during a period when many services had just refreshed their caches with the old key set, leaving up to 24 hours before they would pick up the new key.

2. **No coordinated cache flush step in the rotation runbook**: The rotation runbook did not include a step to force a JWKS cache flush on all resource servers after the new key was added to the JWKS endpoint. This was an assumed implicit step that was never formalized.

## Resolution

1. Identified all services with JWKS caching enabled and their configured TTLs
2. Initiated JWKS cache flush on API Gateway (immediate, no restart required)
3. Performed rolling restarts of microservices to force JWKS re-fetch
4. Confirmed new key ID (`kid`) present in all service JWKS caches via introspection endpoint

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add explicit JWKS cache flush step to key rotation runbook | Platform team | P1 | 2024-12-12 | Completed |
| Standardize maximum JWKS cache TTL to 1 hour across all services | Platform team | P1 | 2025-01-15 | In progress |
| Add JWKS key ID monitoring alert when new key not detected within 2 hours of rotation | SRE | P2 | 2025-01-20 | Pending |
| Document per-service JWKS cache configuration in service registry | On-call | P3 | 2025-02-01 | Pending |

## Lessons Learned

- **What went well**: The 7-day old-key retention period meant no existing valid tokens became permanently invalid. Alerting detected the issue within 11 minutes of the first 401 errors.
- **What went poorly**: The rotation runbook did not include cache invalidation steps. This was a known gap that had not been acted on. The 4-hour recovery time was entirely due to manually restarting ~15 services one at a time.
- **What was lucky**: The rotation occurred during business hours with the full team available. An off-hours rotation would have significantly extended the impact window.
