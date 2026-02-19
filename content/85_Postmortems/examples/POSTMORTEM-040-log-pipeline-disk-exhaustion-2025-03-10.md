---
id: POSTMORTEM-040
type: postmortem
title: Log Pipeline Disk Exhaustion 2025-03-10
status: review
owner: On-Call Engineer
created: '2025-01-08T14:53:51.025Z'
updated: '2025-09-19T18:38:44.310Z'
tags:
  - postmortem
  - monitoring-stack
summary: Log Pipeline Disk Exhaustion 2025-03-10
incident_number: INC-741
severity: SEV-1
incident_date: '2024-03-05'
detection_time: '2026-06-19T03:45:27.809Z'
resolution_time: '2026-10-16T14:03:15.783Z'
total_duration: ~1 hour
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-072
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 10, 2025, the Log Aggregation Pipeline's SQL Server instance ran out of disk space, halting log ingestion for approximately 1 hour. The disk exhaustion was caused by an unexpected 4x spike in log volume from a single service (the Alert Management Service) that had introduced verbose debug logging in a production deployment without an on-call notification. SQL Server's log data files grew faster than the scheduled automated cleanup could handle, filling the 2TB data volume to 100% and causing the ingestion API to return 503 errors to all Fluent Bit agents.

## Timeline

- **02:15** - Alert Management Service deploys a change that accidentally enables `DEBUG` log level in production
- **02:15** - Log ingestion volume spikes 400% from baseline (from 1.2GB/hour to 4.8GB/hour)
- **03:45** - SQL Server data volume reaches 100%; log ingestion API returns 503
- **03:47** - `log_pipeline_ingestion_error_rate_high` alert fires; on-call acknowledges
- **03:52** - On-call identifies disk exhaustion via SQL Server monitoring queries
- **04:00** - Manually truncated oldest 2 days of log data to free 200GB
- **04:05** - Log ingestion resumes; Fluent Bit agents begin retrying buffered logs
- **04:15** - Log volume still elevated; identifies Alert Management Service as source
- **04:20** - Alert Management Service emergency fix deployed to restore `INFO` log level
- **04:45** - Log volume returns to baseline; incident closed

## Impact

- **Duration**: ~1 hour of log ingestion halted (03:47-04:45 UTC)
- **Log data loss**: ~2 days of logs truncated to free disk space; older logs not recoverable
- **Alert coverage gap**: Log-based alerting rules were not evaluating during the ingestion outage, creating a 1-hour blind spot for error-rate alerts driven by log volume
- **Fluent Bit buffer overflow**: On 4 nodes, Fluent Bit's on-disk buffer was exceeded during the outage, causing loss of approximately 8 minutes of log data from those nodes

## Root Cause Analysis

1. **Accidental debug logging in production**: A developer set `LOG_LEVEL=debug` in a staging environment config file and accidentally included it in the production Kubernetes ConfigMap diff. The code review did not catch this because the ConfigMap change appeared in a large diff alongside application code changes.

2. **No log volume rate-of-change alerting**: The `log_pipeline_disk_utilization_warn` alert only fires at 80% disk utilization — a static threshold. It did not detect the sudden 4x volume spike as anomalous. A rate-of-change alert (disk fill rate) would have fired 90 minutes before exhaustion, providing time for intervention.

## Resolution

1. Identified SQL Server disk exhaustion as root cause
2. Truncated 2 days of the oldest indexed log data to free 200GB
3. Identified Alert Management Service as the volume spike source via per-service log volume metrics
4. Deployed emergency fix to restore INFO log level in Alert Management Service
5. Verified log volume returned to baseline and ingestion was stable

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add log volume rate-of-change alert (> 2x baseline for 10 minutes) | SRE | P1 | 2025-03-14 | Completed |
| Add per-service log volume breakdown dashboard | Monitoring Eng | P1 | 2025-03-17 | Completed |
| Add pre-deploy check: validate LOG_LEVEL is not debug in production ConfigMaps | Platform | P1 | 2025-03-21 | Completed |
| Increase SQL Server data volume from 2TB to 3TB | Infra | P2 | 2025-03-28 | Completed |
| Implement automated log volume anomaly detection | Monitoring Eng | P3 | 2025-04-30 | In progress |

## Lessons Learned

- **What went well**: The ingestion error rate alert fired promptly (2 minutes after disk exhaustion). The on-call identified disk exhaustion quickly using SQL Server monitoring queries.
- **What went poorly**: A 4x log volume spike went undetected for 90 minutes before causing an outage. Static disk threshold alerting is insufficient for detecting volume-driven exhaustion events.
- **What was lucky**: The log pipeline's Fluent Bit agents buffer to disk and retry, so most logs were eventually ingested after the outage cleared. Only 8 minutes of data from 4 nodes was permanently lost.
