---
id: POSTMORTEM-008
type: postmortem
title: SSO Provider Cascade Failure 2025-02-14
status: accepted
owner: Incident Commander
created: '2024-08-21T16:57:39.041Z'
updated: '2026-06-24T04:20:07.654Z'
tags:
  - postmortem
  - user-authentication
summary: SSO Provider Cascade Failure 2025-02-14
incident_number: INC-169
severity: SEV-2
incident_date: '2026-10-17'
detection_time: '2025-08-23T09:49:31.446Z'
resolution_time: '2025-01-23T02:14:54.626Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-017
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 14, 2025, the Auth Service experienced a 15-minute cascade failure triggered by an Okta service degradation. The Auth Service's SAML assertion validation path does not have a circuit breaker on the IdP metadata fetch call; when Okta's SAML metadata endpoint became slow (>10s response time), goroutines stacked up waiting for responses, eventually exhausting the HTTP worker pool and causing the auth service to become unresponsive for all traffic — including users not using Okta SSO.

The cascade was stopped by deploying an emergency configuration change to reduce the IdP metadata fetch timeout from 30s to 3s, which allowed the worker pool to drain.

## Timeline

- **09:32** - Okta begins experiencing elevated response times globally (per Okta status page)
- **09:34** - SAML assertion validation calls to Okta metadata endpoint begin timing out at 30s
- **09:36** - HTTP worker pool goroutines begin accumulating waiting for Okta responses
- **09:41** - Auth service worker pool exhausted; all requests begin returning 503
- **09:43** - `auth_service_availability_critical` alert fires. On-call acknowledges.
- **09:49** - On-call identifies goroutine leak via pprof endpoint. Okta degradation confirmed on status page.
- **09:52** - Emergency config change to reduce IdP metadata timeout from 30s to 3s submitted
- **09:54** - Config change deployed. Worker pool begins draining as Okta calls time out quickly.
- **09:57** - Auth service recovers. Error rate drops to baseline.
- **10:11** - Okta degradation resolves. Full Okta SSO functionality restored.
- **10:20** - Incident formally closed.

## Impact

- **Duration**: ~15 minutes (09:41 - 09:57 UTC)
- **Users affected**: All users attempting any authentication, regardless of SSO provider
- **Login failures**: Approximately 3,800 login attempts failed during the full outage window
- **Cascading effect**: Users on local authentication and non-Okta SSO were affected despite not using Okta
- **SLA impact**: 15-minute full outage window exceeded the monthly incident budget
- **Customer communications**: Status page updated at 09:48

## Root Cause Analysis

1. **No circuit breaker on IdP metadata fetch**: The SAML assertion validation path synchronously fetches IdP metadata (XML signing certificates) on each validation call with a 30-second timeout. When Okta became slow, these calls held goroutines open for the full 30-second timeout before failing. With a validation rate of ~40 requests/second and 30 goroutines per request, the 300-goroutine worker pool was exhausted within ~2.5 minutes.

2. **Shared worker pool across all auth pathways**: All auth traffic (SSO, local login, token refresh) shares the same HTTP worker pool. A slow external dependency in one pathway (Okta) starved resources from all other pathways, causing a full service outage rather than a degraded SSO experience.

## Resolution

1. Identified goroutine accumulation via pprof heap and goroutine dump
2. Deployed emergency configuration change reducing IdP metadata timeout to 3s
3. Worker pool drained as in-flight Okta calls returned quickly with timeout errors
4. Confirmed recovery and monitored until Okta fully recovered

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement circuit breaker on all IdP metadata fetch calls | Auth team | P1 | 2025-02-21 | Completed |
| Move SSO validation to a separate worker pool isolated from local auth | Auth team | P1 | 2025-03-07 | In progress |
| Reduce default IdP metadata timeout from 30s to 5s | Auth team | P1 | 2025-02-18 | Completed |
| Add per-IdP health check and automatic circuit open on consecutive failures | Auth team | P2 | 2025-03-15 | Pending |
| Add runbook section for external IdP degradation | On-call | P2 | 2025-02-21 | Completed |

## Lessons Learned

- **What went well**: pprof endpoint was available and provided immediate insight into goroutine accumulation. The emergency config change was deployable in under 2 minutes. Recovery was complete within 3 minutes of the config change.
- **What went poorly**: Shared worker pool design allowed a single external IdP degradation to take down all authentication. This is a fundamental architectural weakness that needs to be addressed structurally, not just with a circuit breaker.
- **What was lucky**: The pprof endpoint was enabled on the auth service. If it had been disabled, diagnosing the goroutine leak would have taken significantly longer.
