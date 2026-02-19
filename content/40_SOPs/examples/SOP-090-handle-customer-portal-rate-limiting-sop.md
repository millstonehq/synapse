---
id: SOP-090
type: sop
title: Handle Customer Portal Rate Limiting SOP
status: draft
owner: Release Manager
created: '2024-09-01T01:13:29.798Z'
updated: '2025-12-10T20:40:24.863Z'
tags:
  - sop
  - customer-portal
summary: Handle Customer Portal Rate Limiting SOP
related_process: PROCESS-069
related_systems:
  - SYSTEM-045
example: true
---

## Preconditions

- A rate limiting issue has been identified: customers receiving 429 responses, legitimate traffic being throttled, or rate limit thresholds needing adjustment
- The affected API endpoint(s) and the triggering account or IP range have been identified
- On-call engineer has opened an investigation ticket

## Materials/Access

- Access to the API gateway or rate limiting service console (Kong, AWS API Gateway, or equivalent)
- Access to portal API logs in Datadog filtered by status code 429
- Access to the rate limiting configuration in the portal configuration repository
- Change ticket ID if a threshold adjustment is needed

## Procedure

1. Open Datadog and filter portal API logs for HTTP 429 responses; identify the affected endpoints, customer accounts, or IP ranges generating the 429s.
2. Determine the cause category: (a) legitimate traffic spike by a specific customer, (b) misconfigured rate limit threshold, (c) bot or scraping traffic, or (d) a portal bug causing retry loops.
3. For a legitimate customer traffic spike: identify the customer account, review their usage pattern, and determine whether a temporary limit increase is warranted.
4. If a temporary increase is warranted, open a change ticket and update the rate limit configuration for the affected customer tier or endpoint in the API gateway console.
5. For bot or scraping traffic: identify the source IP range in the API gateway logs, add it to the blocklist, and escalate to the security team for further investigation.
6. For a portal retry loop bug: identify the endpoint and the client-side code causing excessive retries; implement a fix or apply an emergency circuit breaker in the API gateway.
7. If the root cause is a misconfigured threshold that is too restrictive, open a change ticket to adjust the threshold, have it reviewed by an Engineering Lead, and apply the change.
8. Monitor the API gateway for 10 minutes after changes; confirm 429 rate is returning to near-zero for legitimate traffic.
9. Post resolution status in #customer-portal-incidents and update the investigation ticket with root cause and actions taken.

## Validation

- API gateway metrics show 429 response rate returning to baseline (typically <0.1% of requests)
- Affected customers can complete their portal workflows without interruption
- No legitimate customer traffic is being throttled at the adjusted thresholds
- Datadog alert for `portal_api_429_rate_high` has resolved

## Rollback

1. If a rate limit threshold change causes unintended consequences (e.g., allowing abuse traffic), revert the threshold to its previous value via the API gateway console.
2. Update the change ticket to document the rollback with timestamp and reason.
3. Monitor for 10 minutes after the revert to confirm the 429 rate behavior returns to the pre-change state.
4. Re-evaluate the correct threshold value before re-applying any changes.
