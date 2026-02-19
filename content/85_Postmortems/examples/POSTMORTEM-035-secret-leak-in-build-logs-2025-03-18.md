---
id: POSTMORTEM-035
type: postmortem
title: Secret Leak in Build Logs 2025-03-18
status: approved
owner: On-Call Engineer
created: '2025-08-21T14:12:46.020Z'
updated: '2025-07-02T22:47:32.676Z'
tags:
  - postmortem
  - ci-cd-platform
summary: Secret Leak in Build Logs 2025-03-18
incident_number: INC-646
severity: SEV-3
incident_date: '2025-01-02'
detection_time: '2024-03-30T14:00:12.026Z'
resolution_time: '2024-11-11T09:50:34.461Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-062
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 18, 2025, a CI build job for the `integrations-service` printed an AWS access key ID and secret to the build log. A developer had added a debug `echo` statement to troubleshoot a credentials issue during development and inadvertently merged the change. The log was accessible to all engineers with CI read access for approximately 2 hours before detection. The credentials were rotated within 30 minutes of detection. No unauthorized use of the leaked credentials was detected in AWS CloudTrail.

## Timeline

- **09:12** - `integrations-service` build job runs; AWS credentials printed to log via debug echo statement
- **09:14** - Build completes successfully; log retained in CI log storage
- **11:03** - Security monitoring tool (truffleHog log scan) flags the build log containing an AWS credential pattern
- **11:04** - Security on-call engineer receives alert, confirms the credential is a live access key
- **11:06** - AWS access key invalidated via IAM console
- **11:10** - New access key generated and rotated into Kubernetes Secrets
- **11:20** - Build log archived with restricted access; access audit requested from AWS CloudTrail
- **11:45** - CloudTrail review complete: no unauthorized API calls observed with the leaked key
- **12:00** - PR containing the echo statement identified; author notified, remediation PR merged
- **13:00** - Incident closed after final credential audit

## Impact

- **Duration of exposure**: ~2 hours (09:12 - 11:06 UTC)
- **Credential type**: AWS IAM access key (read/write access to S3 integration buckets)
- **Unauthorized access confirmed**: None detected
- **Users affected**: None; no service interruption occurred
- **Compliance notification**: Security team notified per security incident response SOP

## Root Cause Analysis

1. **Debug credential echo merged to main**: A developer added `echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"` to a build script for local troubleshooting and did not remove it before merging. Code review did not catch the sensitive echo statement.

2. **No secret scanning in CI pre-merge**: There was no automated secret scanning step in the CI pipeline that would have blocked the merge of a build script containing a credential reference in plaintext echo.

## Resolution

1. Security on-call identified and confirmed live credential in build log
2. AWS access key revoked immediately via IAM console
3. New credential rotated into Kubernetes Secrets for `integrations-service`
4. CloudTrail audit confirmed no unauthorized use
5. Build log access restricted; PR with debug echo reverted

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add truffleHog/gitleaks secret scanning as required CI pre-merge step | Platform team | P1 | 2025-03-25 | Completed |
| Implement automatic build log masking for known credential patterns | Platform team | P1 | 2025-03-28 | Completed |
| Rotate all CI/CD service account credentials as a precaution | Security team | P2 | 2025-03-22 | Completed |
| Add "no secrets in echo/print" to CI/CD coding guidelines | Platform team | P3 | 2025-04-01 | Completed |

## Lessons Learned

- **What went well**: truffleHog log scanning detected the credential within 2 hours. Rotation was fast. No unauthorized use occurred.
- **What went poorly**: There was no pre-merge secret scanning. The code review did not catch a plaintext credential echo, which is a known anti-pattern.
- **What was lucky**: The exposure window was short and the credential access pattern was narrow (S3 only). A broader credential (e.g., admin IAM key) would have been a SEV-1.
- **Process improvement**: Secret scanning in CI is now mandatory and blocks merge. Build log masking is enabled for all jobs.
