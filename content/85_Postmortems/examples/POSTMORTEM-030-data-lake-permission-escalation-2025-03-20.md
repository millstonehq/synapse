---
id: POSTMORTEM-030
type: postmortem
title: Data Lake Permission Escalation 2025-03-20
status: approved
owner: Incident Commander
created: '2024-01-06T15:55:50.225Z'
updated: '2026-06-28T03:35:09.292Z'
tags:
  - postmortem
  - data-pipeline
summary: Data Lake Permission Escalation 2025-03-20
incident_number: INC-551
severity: SEV-2
incident_date: '2026-10-19'
detection_time: '2025-02-24T13:47:48.607Z'
resolution_time: '2026-06-14T05:44:27.765Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-059
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 20, 2025, a misconfigured IAM role update granted a data transformation ECS task write access to raw data lake S3 partitions outside its intended scope. The task, which should only have write access to a specific transformed output prefix, briefly had write access to all `s3://data-lake-prod/raw/` partitions. The misconfiguration was present for approximately 15 minutes before being detected and revoked. No data was written to out-of-scope partitions during the window.

The incident was detected by an AWS CloudTrail alert on anomalous S3 write attempts from the transformation task role to raw partition paths. The IAM policy was corrected and re-applied within 15 minutes of detection.

## Timeline

- **14:22** - Infrastructure engineer applies IAM policy update for a new transformation task; copy-paste error includes `s3://data-lake-prod/raw/*` in the write policy instead of `s3://data-lake-prod/transformed/*`
- **14:25** - Policy propagation complete; transformation task now has write access to raw partitions
- **14:28** - Transformation task executes as scheduled; no writes to raw partitions occur (task does not have code paths to write to raw paths)
- **14:35** - CloudTrail anomaly alert fires: `TransformationTask role performing S3 PutObject on raw/ prefix` (triggered by a presigned URL test in a separate task, not the transformation task itself)
- **14:38** - Security team and on-call notified; IAM policy investigation begins
- **14:42** - Root cause identified: overly broad write policy in the transformation task role
- **14:48** - Corrected IAM policy applied; transformation task role restricted back to intended prefix
- **14:50** - Incident contained; investigation of all S3 write activity during 14:22–14:48 window begins
- **15:05** - Investigation complete; zero writes to raw partitions confirmed from the transformation task role

## Impact

- **Duration**: 15 minutes of excess IAM permissions (14:22 - 14:48 UTC)
- **Data modified**: Zero — no writes occurred to out-of-scope raw partitions
- **Blast radius**: Transformation task role had write access to all 40 raw source system prefixes during the window
- **Detection time**: 13 minutes from misconfiguration to alert
- **SLA impact**: None — pipeline execution was not interrupted

## Root Cause Analysis

1. **Manual IAM policy editing without review**: The infrastructure engineer edited the IAM policy document directly in the AWS console without peer review. The copy-paste error was not caught because there was no automated validation of IAM policies before application.

2. **Overly broad alerting conditions**: The CloudTrail alert was triggered by a separate presigned URL test, not by the transformation task itself. Without this coincidental trigger, the misconfiguration might have persisted until the next scheduled IAM audit.

## Resolution

1. Identified the misconfigured write policy via IAM policy diff comparison
2. Applied corrected policy restricting the transformation task role to `s3://data-lake-prod/transformed/*` write access only
3. Performed forensic analysis of all S3 write activity from the task role during the 26-minute window
4. Confirmed zero unauthorized writes; no data integrity impact

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Require peer review for all production IAM policy changes | Security + Infra | P1 | 2025-03-25 | Completed |
| Implement IAM policy validation CI step checking for overly broad S3 write permissions | Infra | P1 | 2025-04-05 | In Progress |
| Full IAM permission audit for all 23 data pipeline service accounts | Security | P1 | 2025-04-15 | In Progress |
| Add CloudTrail alert for any data lake role writing outside its designated prefix | SRE | P2 | 2025-04-01 | Completed |

## Lessons Learned

- **What went well**: CloudTrail alerting detected the overly broad permission within 13 minutes. No data was modified during the window.
- **What went poorly**: Manual IAM policy editing without peer review or automated validation is a high-risk practice. The organization lacked a gate preventing production IAM changes without approval.
- **What was lucky**: The transformation task's code paths do not include writes to raw partition paths. If they had, unintended writes would have been easy to make before detection.
