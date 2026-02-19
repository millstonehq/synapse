---
id: POSTMORTEM-033
type: postmortem
title: Artifact Registry Corruption 2025-02-11
status: draft
owner: Incident Commander
created: '2025-05-17T07:32:33.802Z'
updated: '2026-10-22T13:36:58.331Z'
tags:
  - postmortem
  - ci-cd-platform
summary: Artifact Registry Corruption 2025-02-11
incident_number: INC-644
severity: SEV-1
incident_date: '2025-02-05'
detection_time: '2025-02-11T23:40:08.151Z'
resolution_time: '2025-05-02T08:42:50.790Z'
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

On February 11, 2025, a storage backend anomaly in the Harbor container registry caused the manifest index for 14 recently-pushed container images to become corrupted. Affected images returned `manifest unknown` errors when pulled by the Deployment Controller, blocking deployments for the affected services. The Artifact Registry team identified the corruption via checksum validation, restored affected manifests from the Harbor database backup, and verified integrity. Total resolution time was approximately 2 hours.

No data was permanently lost. All 14 artifacts were recovered from backup. Three scheduled deployments were delayed by 90 minutes while the restore was in progress.

## Timeline

- **09:30** - Harbor garbage collection job runs (scheduled nightly)
- **09:34** - Garbage collection job exits with an unexpected error mid-run
- **10:15** - Deployment Controller attempts to pull `api-gateway:sha-a3f291c`; receives `manifest unknown` error
- **10:17** - Deployment for `api-gateway` fails. On-call engineer alerted.
- **10:22** - On-call investigates; finds manifest pull failing for 14 artifacts pushed after 09:00
- **10:25** - Harbor admin confirms corrupted manifest index entries in the registry database
- **10:30** - Incident escalated to Artifact Registry team lead
- **10:45** - Database backup from 09:00 UTC identified as recovery source
- **11:10** - Restore of 14 manifest records completed from backup
- **11:15** - Checksum verification confirms integrity of restored artifacts
- **11:20** - Blocked deployments re-triggered and complete successfully
- **11:30** - Incident closed after monitoring period

## Impact

- **Duration**: ~2 hours (10:15 - 11:30 UTC)
- **Artifacts corrupted**: 14 container image manifests
- **Deployments blocked**: 3 scheduled deployments delayed by 90 minutes
- **Data loss**: None — all artifacts restored from backup
- **SLA impact**: Artifact registry availability dropped below 99.99% for February

## Root Cause Analysis

1. **Garbage collection bug in Harbor 2.9.1**: An edge case in Harbor's garbage collection algorithm erroneously marked non-expired manifests as eligible for deletion when a large number of image tags were processed in a single run. The bug was present in Harbor 2.9.1 and patched in 2.9.2, released one week after this incident.

2. **No post-GC integrity verification**: The nightly garbage collection job had no step to verify that all referenced manifests remained valid after the run. An automated checksum scan would have detected the corruption at 09:34 instead of 10:15 when the first deployment pull failed.

## Resolution

1. Identified the corrupted manifest records via Harbor database inspection
2. Restored 14 manifest records from the nightly backup (09:00 UTC snapshot)
3. Ran checksum verification against all restored artifacts to confirm integrity
4. Re-triggered blocked deployments
5. Updated Harbor to 2.9.2 during the next maintenance window (Feb 14)

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Upgrade Harbor to 2.9.2 (patches GC bug) | Platform team | P1 | 2025-02-14 | Completed |
| Add post-GC manifest integrity check as a required step | Platform team | P1 | 2025-02-20 | Completed |
| Automate backup verification to run daily | Platform team | P2 | 2025-02-28 | Completed |
| Add alert for garbage collection job failures | Platform team | P2 | 2025-02-28 | Completed |

## Lessons Learned

- **What went well**: Backup was recent (< 1 hour old) and restore was clean. Recovery was systematic and thorough.
- **What went poorly**: There was no alert when the GC job exited with an error. The corruption was not detected until a deployment failed 41 minutes later.
- **What was lucky**: The corrupted artifacts had all been pushed after the backup, so the backup was sufficient for a full restore with no data loss.
- **Process improvement**: Garbage collection jobs must have explicit failure alerting and post-run integrity checks going forward.
