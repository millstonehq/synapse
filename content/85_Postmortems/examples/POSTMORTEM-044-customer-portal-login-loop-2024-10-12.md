---
id: POSTMORTEM-044
type: postmortem
title: Customer Portal Login Loop 2024-10-12
status: approved
owner: On-Call Engineer
created: '2025-08-19T00:40:20.858Z'
updated: '2026-04-19T22:35:04.210Z'
tags:
  - postmortem
  - customer-portal
summary: Customer Portal Login Loop 2024-10-12
incident_number: INC-835
severity: SEV-1
incident_date: '2025-10-19'
detection_time: '2024-03-12T00:21:39.086Z'
resolution_time: '2024-12-11T03:18:18.421Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-087
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On October 12, 2024, all customers attempting to log into the Customer Portal were caught in an infinite redirect loop for approximately 1 hour. A deploy to the portal authentication middleware introduced a regression where the post-login redirect URL was incorrectly constructed when the session cookie was set with a trailing slash on the portal domain. Customers were unable to log in, and the portal was effectively inaccessible for authenticated sessions.

The issue was detected at 08:41 UTC via alert on authentication success rate. The deploy was rolled back at 09:43 UTC, restoring login functionality.

## Timeline

- **08:15** - Portal authentication middleware deploy shipped to production
- **08:38** - First customer support ticket reports login redirect loop
- **08:41** - `portal_auth_success_rate_low` alert fires (success rate dropped from 99.2% to 3.1%)
- **08:45** - On-call acknowledges; identifies deploy at 08:15 as likely cause
- **08:52** - On-call attempts to reproduce the loop in staging; cannot (staging uses different domain config)
- **09:10** - Auth team engineer joins; reviews the middleware diff; spots redirect URL construction change
- **09:25** - Root cause confirmed: `returnTo` parameter appended twice when session domain ends with `/`
- **09:43** - Deploy rolled back; login success rate recovers to 99.4% within 2 minutes
- **10:00** - Incident closed after 17-minute stable observation window

## Impact

- **Duration**: ~1 hour (08:38 - 09:43 UTC)
- **Users affected**: All customers attempting portal login during the window
- **Authentication success rate**: Dropped to 3.1% (down from 99.2%)
- **SLA impact**: Portal was technically available but inaccessible for authenticated sessions — SLA breach under strict interpretation
- **Customer communications**: Status page updated at 08:50; 89 support tickets received

## Root Cause Analysis

1. **Redirect URL double-append bug**: The updated middleware constructed the post-login redirect URL by appending the `returnTo` query parameter to a base URL. When the portal domain in session configuration ended with `/`, the parameter was appended as `//returnTo=...`, causing the browser to interpret it as a new path redirect and loop indefinitely.

2. **Staging environment domain mismatch**: The staging environment uses `portal-staging.example.com` without a trailing slash, so the bug could not be reproduced in staging before the deploy. Production uses a domain alias configuration that includes a trailing slash.

## Resolution

1. Rolled back the authentication middleware deploy
2. Confirmed login success rate recovered
3. Monitored for 17 minutes before closing

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Fix redirect URL construction to strip trailing slashes before parameter append | Auth team | P1 | 2024-10-14 | Completed |
| Align staging domain configuration with production (no trailing slash) | Platform team | P1 | 2024-10-18 | Completed |
| Add E2E test: login flow succeeds from portal root, subpath, and with returnTo parameter | QA | P2 | 2024-10-25 | Completed |
| Add `portal_auth_success_rate_low` alert to SEV-1 auto-escalation | SRE | P2 | 2024-10-25 | Completed |

## Lessons Learned

- **What went well**: Alert fired within 3 minutes of the bug becoming active. Auth team engineer identified the root cause quickly once they reviewed the diff.
- **What went poorly**: The staging environment configuration differed from production in a way that prevented reproduction. Environment parity gaps are a recurring risk.
- **What was lucky**: The rollback was clean with no data migration required. Login success recovered within 2 minutes of rollback.
