---
id: SOP-060
type: sop
title: Data Pipeline Rollback SOP
status: deprecated
owner: SRE Lead
created: '2025-04-02T18:02:55.284Z'
updated: '2025-09-01T11:41:20.551Z'
tags:
  - sop
  - data-pipeline
summary: Data Pipeline Rollback SOP
related_process: PROCESS-032
related_systems:
  - SYSTEM-030
example: true
---

## Preconditions

- A pipeline deployment has been identified as producing incorrect outputs or causing downstream failures
- The previous stable version of the pipeline is known (commit SHA or image tag)
- Downstream consumers have been notified that the rollback is in progress
- A rollback ticket has been opened with the scope of affected partitions

## Materials/Access

- Access to the pipeline orchestration UI and CI/CD deployment system
- Write access to the target data lake storage or warehouse
- Access to #data-releases Slack channel

## Procedure

1. Post in #data-releases: "ROLLING BACK pipeline [pipeline_name]. Reason: [brief description]. Affected dates: [range]."
2. Pause the current pipeline in the orchestration platform to halt new runs immediately.
3. Re-deploy the previous stable version using the CI/CD system, specifying the last known-good commit SHA.
4. Confirm the orchestration UI reflects the reverted pipeline definition.
5. Identify all output partitions written by the faulty version; flag them as suspect in the data catalog.
6. Delete or overwrite the suspect output partitions using the standard idempotent delete-and-reload pattern.
7. Un-pause the pipeline and trigger a backfill run for the affected date range using the rolled-back version.
8. Monitor the backfill run through completion; verify output record counts match pre-incident expectations.
9. Post in #data-releases: "Pipeline rollback complete. Partitions [range] reprocessed. Downstream consumers unblocked."

## Validation

- The orchestration UI shows the previous stable pipeline version active in production
- All suspect output partitions have been reprocessed and contain correct data
- Downstream consumers confirm they are receiving correct data for the affected date range
- No new data quality alerts have fired following the rollback

## Rollback

1. If the rollback itself fails (previous version also produces errors), pause the pipeline again.
2. Escalate to the Pipeline Owner and Data Platform Team for immediate investigation.
3. Keep the suspect partitions flagged and halt downstream propagation until a fix is confirmed.
4. Document all attempted rollback steps and observed errors in the rollback ticket.
5. Do not re-enable the pipeline until the root cause is identified and a fix is validated in staging.
