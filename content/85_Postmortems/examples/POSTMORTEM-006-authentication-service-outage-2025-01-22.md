---
id: POSTMORTEM-006
type: postmortem
title: Authentication Service Outage 2025-01-22
status: approved
owner: On-Call Engineer
created: '2024-08-17T02:30:27.332Z'
updated: '2026-04-28T23:18:47.577Z'
tags:
  - postmortem
  - user-authentication
summary: Authentication Service Outage 2025-01-22
incident_number: INC-167
severity: SEV-2
incident_date: '2026-11-28'
detection_time: '2026-08-22T12:18:13.773Z'
resolution_time: '2025-04-06T18:12:41.534Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-018
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 22, 2025, the Authentication Service experienced a 2-hour outage that prevented all users from logging in. The root cause was a cascading failure triggered by a misconfigured TLS certificate renewal that took the OAuth Authorization Server's token endpoint offline. Users with existing valid sessions were unaffected, but new logins, token refreshes, and service-to-service token grants all failed during the window.

The incident was detected by automated alerting 4 minutes after the first failures. Resolution required rolling back the certificate configuration and restarting the affected pods. Full recovery was confirmed at 14:18 UTC after a 30-minute stable observation window.

## Timeline

- **12:06** - Automated certificate renewal job runs on the OAuth Authorization Server pod startup
- **12:08** - New certificate deployed with incorrect SAN (Subject Alternative Name) missing the internal service hostname
- **12:09** - mTLS handshakes from Session Management Service to OAuth Server begin failing silently
- **12:13** - Login error rate spikes to 100%. Users unable to complete authorization code flow.
- **12:17** - `auth_login_error_rate_critical` alert fires. On-call engineer acknowledges.
- **12:22** - On-call identifies TLS handshake errors in OAuth Server logs
- **12:31** - Root cause narrowed to certificate SAN mismatch. Previous certificate retrieved from Vault backup.
- **12:38** - Certificate rollback applied to staging to validate fix
- **12:45** - Certificate rollback applied to production. Pod restart initiated.
- **12:52** - Login success rate recovers to 99.8%. Monitoring continues.
- **13:18** - Incident formally closed after 30-minute stable observation window.

## Impact

- **Duration**: ~2 hours (12:09 - 13:18 UTC)
- **Users affected**: All users attempting new logins or token refreshes; existing sessions unaffected
- **Logins blocked**: Approximately 14,000 failed login attempts during the window
- **Service-to-service impact**: 3 downstream services that use client credentials grants were also affected
- **SLA impact**: Monthly availability for the auth service dropped below the 99.95% SLO
- **Customer communications**: Status page updated at 12:25, incident resolved notification at 13:20

## Root Cause Analysis

1. **Certificate renewal automation produced an incorrect SAN**: The automated renewal script had a bug introduced in a dependency update that caused it to generate a certificate with only the external-facing hostname in the SAN, omitting the internal Kubernetes service hostname. mTLS connections from peer services that connect via the internal hostname were rejected.

2. **No automated certificate validation after renewal**: The certificate renewal job did not include a post-issuance validation step that would verify the SAN list against a known-good configuration. The bad certificate passed through to production without being caught.

## Resolution

1. Identified the SAN mismatch by comparing the new certificate's SAN list against the previous certificate
2. Retrieved the previous certificate from HashiCorp Vault (retained for 90 days post-rotation)
3. Applied the rollback certificate to all OAuth Authorization Server pods
4. Performed a rolling restart to pick up the new certificate without downtime
5. Monitored for 30 minutes to confirm stable operation

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add SAN validation step to certificate renewal automation | Platform team | P1 | 2025-01-29 | Completed |
| Add post-renewal integration test that verifies mTLS handshake from each consuming service | Platform team | P1 | 2025-02-05 | Completed |
| Add `auth_cert_san_mismatch` alert based on TLS handshake error logs | SRE | P2 | 2025-02-12 | In progress |
| Document certificate rollback procedure in auth runbook | On-call | P2 | 2025-02-05 | Completed |
| Expand certificate retention in Vault from 90 days to 180 days | Platform team | P3 | 2025-03-01 | Pending |

## Lessons Learned

- **What went well**: Alerting fired within 4 minutes of the first failures. The previous certificate was available in Vault, making rollback straightforward. On-call correctly isolated the root cause to TLS within 14 minutes.
- **What went poorly**: The certificate renewal automation had no post-issuance validation. A simple check of the SAN list would have caught this before production. Existing tests only validated certificate expiry, not certificate content.
- **What was lucky**: The previous certificate was still valid (30 days remaining) and available in Vault. If it had been deleted or expired, recovery would have required generating a new certificate, adding significant time to the outage.
