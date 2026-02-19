---
id: POSTMORTEM-038
type: postmortem
title: Prometheus Data Loss 2025-02-19
status: review
owner: Incident Commander
created: '2024-12-29T21:38:18.469Z'
updated: '2026-01-12T12:23:37.835Z'
tags:
  - postmortem
  - monitoring-stack
summary: Prometheus Data Loss 2025-02-19
incident_number: INC-739
severity: SEV-1
incident_date: '2024-12-10'
detection_time: '2025-09-26T14:17:32.525Z'
resolution_time: '2024-01-28T05:55:48.203Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-071
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On February 19, 2025, a Prometheus TSDB compaction crash caused the loss of approximately 2 hours of metric data across all monitored services. The crash occurred when a compaction job attempted to merge overlapping blocks from a prior interrupted compaction (itself a consequence of the January 30 disk-full incident). The crash loop caused both HA Prometheus instances to restart repeatedly, preventing scraping for the duration. Unlike the January 30 blackout, some data was permanently lost — the WAL covering the crash window was partially corrupted.

The incident was detected automatically by the new Prometheus self-monitoring alerts deployed after POSTMORTEM-036 and was acknowledged within 4 minutes.

## Timeline

- **09:12** - Prometheus-0 begins TSDB compaction; encounters overlapping blocks from incomplete Jan 30 compaction
- **09:14** - Compaction panics: `unexpected block overlap` error; pod crashes and restarts
- **09:15** - `prometheus_tsdb_compaction_failed_total` alert fires; on-call acknowledges within 4 minutes
- **09:19** - Prometheus-1 also encounters the same overlapping blocks and crashes
- **09:22** - Both HA instances in crash loop; metric scraping halted
- **09:30** - On-call identifies overlapping block files via `tsdb` CLI; begins manual block repair
- **09:55** - Corrupted blocks deleted manually; Prometheus instances restart cleanly
- **10:00** - Scraping resumes; 2-hour data gap confirmed in Grafana (09:12-11:00 UTC)
- **11:00** - Incident closed; 2 hours of metric data confirmed permanently lost

## Impact

- **Duration**: ~2 hours of metric scraping halted (09:12-11:00 UTC)
- **Data loss**: Approximately 2 hours of all service metrics permanently lost (WAL corruption prevented WAL replay)
- **Alert suppression**: All alerting halted for 2 hours
- **SLO impact**: Prometheus monthly SLO dropped below 99.99% target for February
- **Downstream impact**: SLO compliance calculations for February have a 2-hour gap; affected services' monthly availability calculations are estimates for this period

## Root Cause Analysis

1. **Residual state from January 30 incident**: When the disk-full incident on January 30 caused Prometheus to halt mid-compaction, an incomplete compaction left overlapping TSDB blocks. The January 30 remediation (deleting old blocks to free space) did not include verification that no overlapping block state remained.

2. **Missing block integrity check in recovery procedure**: The January 30 recovery runbook had no step to verify TSDB block integrity after disk recovery. A simple `promtool tsdb list` command would have surfaced the overlapping blocks before the February 19 compaction crash.

## Resolution

1. Identified overlapping block files using `promtool tsdb list --human-readable`
2. Deleted the corrupt incomplete blocks from January 30
3. Restarted Prometheus instances; clean compaction cycle completed
4. Confirmed 2-hour data gap is permanent (WAL not recoverable)
5. Updated SLO calculations for affected period with data gap annotation

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add `promtool tsdb list` integrity check to Prometheus recovery runbook | Monitoring Eng | P1 | 2025-02-26 | Completed |
| Run `tsdb` block integrity check on all Prometheus instances post-incident | SRE | P1 | 2025-02-20 | Completed |
| Add alerting on `prometheus_tsdb_compaction_failed_total` > 0 | SRE | P1 | 2025-02-24 | Completed |
| Implement WAL checkpointing improvements to reduce data loss window | Monitoring Eng | P2 | 2025-03-15 | Completed |
| Document disk-full recovery procedure with block integrity verification | Monitoring Eng | P2 | 2025-02-28 | Completed |

## Lessons Learned

- **What went well**: The new Prometheus self-monitoring alerts (deployed post-POSTMORTEM-036) detected the crash loop within 4 minutes. Without those alerts, this incident might have gone undetected for hours as in January.
- **What went poorly**: The January 30 recovery was incomplete — it freed disk space but did not verify TSDB integrity. This created a ticking time bomb that detonated 20 days later.
- **What was lucky**: The crash occurred during business hours when engineers were available. The manual block repair required significant Prometheus internals knowledge that would have been harder to mobilize after hours.
