---
id: POSTMORTEM-010
type: postmortem
title: OAuth Token Leak Incident 2025-03-08
status: review
owner: On-Call Engineer
created: '2024-08-23T02:05:20.670Z'
updated: '2025-03-17T18:56:21.458Z'
tags:
  - postmortem
  - user-authentication
summary: OAuth Token Leak Incident 2025-03-08
incident_number: INC-171
severity: SEV-2
incident_date: '2026-10-13'
detection_time: '2025-08-23T08:58:23.673Z'
resolution_time: '2025-10-21T01:31:32.887Z'
total_duration: ~2 hours
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

On March 8, 2025, a logging configuration change caused OAuth access tokens to be written to application logs in plaintext for approximately 2 hours. The logs were accessible to anyone with read access to the centralized log aggregation system, which includes all engineers and some support staff. An estimated 24,000 access tokens were exposed in logs before the configuration was reverted.

Upon discovery, all exposed tokens were immediately revoked via batch invalidation, and all affected users' refresh tokens were rotated. No evidence of unauthorized access using the leaked tokens was found during the post-incident forensic review.

## Timeline

- **06:00** - A logging verbosity change is deployed to the OAuth Authorization Server to debug a token issuance latency issue. The change inadvertently enables DEBUG-level logging which includes full request/response bodies.
- **06:02** - Access tokens begin appearing in log lines under `response.body.access_token`
- **06:00 - 08:12** - Approximately 24,000 tokens written to logs (2-hour exposure window)
- **08:12** - Security engineer notices access tokens in Datadog log search while investigating an unrelated issue
- **08:15** - Incident declared. Logging configuration reverted immediately.
- **08:18** - Logging configuration rollback confirmed; token logging stopped.
- **08:25** - Batch token revocation script prepared, reviewed, and tested in staging
- **08:35** - Batch revocation of all ~24,000 affected tokens executed against the token blacklist
- **08:48** - Refresh token rotation initiated for all affected user accounts
- **09:15** - Refresh token rotation complete. All 8,400 affected users required to re-authenticate.
- **09:30** - Forensic review of access logs for affected tokens begins
- **11:30** - Forensic review complete. No evidence of unauthorized token use detected.
- **12:00** - Incident closed. Security team begins root cause write-up.

## Impact

- **Duration**: ~2 hours of token exposure (06:00 - 08:15 UTC)
- **Tokens exposed**: ~24,000 access tokens written to logs
- **Users affected**: ~8,400 unique users had active tokens exposed
- **Token revocation**: All 24,000 exposed tokens revoked within 20 minutes of discovery
- **User impact**: ~8,400 users required to re-authenticate due to refresh token rotation
- **Data classification**: Access tokens are classified as secrets under the data classification policy; this constitutes a secret exposure incident requiring security review

## Root Cause Analysis

1. **DEBUG logging included full response bodies with tokens**: The OAuth server's debug logging mode was designed for development environments and included full HTTP response body logging. The log configuration change incorrectly used `LOG_LEVEL=DEBUG` (intended for local debugging only) instead of `LOG_LEVEL=INFO` with additional latency context fields.

2. **No secrets scrubbing in the logging pipeline**: The log aggregation pipeline (Datadog) had no configured scrubbing rules for OAuth access token patterns. A regex rule matching bearer token patterns would have redacted tokens before they were written to the searchable log index.

## Resolution

1. Reverted logging configuration to INFO level immediately on discovery
2. Executed batch token revocation for all tokens issued during the exposure window
3. Rotated refresh tokens for all affected user accounts
4. Conducted forensic review of access logs for evidence of unauthorized token use

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add Datadog log scrubbing rule for OAuth access token patterns (`ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`) | SRE | P1 | 2025-03-10 | Completed |
| Block `LOG_LEVEL=DEBUG` in production configuration validation | Platform team | P1 | 2025-03-12 | Completed |
| Add automated secret-in-log detection to CI (trufflehog on log output samples) | Security team | P2 | 2025-03-31 | In progress |
| Conduct log scrubbing audit across all services for other secret patterns | Security team | P2 | 2025-04-15 | Pending |
| Update data classification policy to explicitly list OAuth tokens as secrets requiring scrubbing | Security team | P3 | 2025-04-15 | Pending |

## Lessons Learned

- **What went well**: A security engineer identified the token exposure within 2 hours through routine log review. Batch revocation was executable quickly because a revocation mechanism already existed. The forensic review found no evidence of unauthorized use.
- **What went poorly**: DEBUG logging should never have been deployable to production without an explicit override and approval. The log scrubbing pipeline had no rules for access token patterns, which is a fundamental gap in the secrets hygiene posture.
- **What was lucky**: Access tokens have a 15-minute expiry. By the time the incident was declared and most tokens were consumed in normal usage, many had already expired naturally, reducing the active exposure window.
