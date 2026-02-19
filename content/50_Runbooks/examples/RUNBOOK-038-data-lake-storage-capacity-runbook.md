---
id: RUNBOOK-038
type: runbook
title: Data Lake Storage Capacity Runbook
status: approved
owner: On-Call Engineer
created: '2024-06-25T02:37:41.357Z'
updated: '2026-02-18T08:10:26.092Z'
tags:
  - runbook
  - data-pipeline
summary: Data Lake Storage Capacity Runbook
example: true
---

## Service

- **System**: [[SYSTEM-030|Data Lake]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #data-incidents
- **Runtime**: S3 / AWS / Iceberg / Delta Lake

## Alerts

- `data_lake_storage_usage_high` - Storage utilization exceeds 80% of provisioned capacity
- `data_lake_storage_growth_anomaly` - Daily storage growth rate exceeds 3x the 7-day average
- `data_lake_write_throttling` - S3 PUT throttling rate exceeds 5% for 10 minutes
- `data_lake_lifecycle_policy_failure` - Automated lifecycle policy job has not run in 48 hours

## Diagnosis Steps

1. **Identify which bucket or prefix is driving growth** - Use the S3 Storage Lens dashboard or run `aws s3 ls s3://[data-lake-bucket]/ --recursive --human-readable --summarize` to identify the largest prefixes.
2. **Check for runaway pipeline writes** - Look for abnormally large partition writes in the pipeline execution logs from the past 24 hours; a pipeline loop or misconfigured backfill can rapidly consume storage.
3. **Check lifecycle policy execution** - Verify that the automated archival and expiry lifecycle policies are executing on schedule; navigate to S3 bucket lifecycle rules and review recent execution logs in CloudWatch.
4. **Identify uncompressed or poorly formatted data** - Check if any recent pipelines are writing uncompressed formats (CSV, uncompressed JSON) instead of Parquet or ORC; these can be 10-20x larger than columnar equivalents.
5. **Review snapshot and temp file accumulation** - Check for orphaned staging files, uncommitted Iceberg snapshots, or abandoned compaction outputs that failed to clean up.

## Remediation Steps

1. **If a runaway pipeline is writing excessive data**: Pause the pipeline immediately, assess the written partitions, and clean up over-written data before resuming.
2. **If lifecycle policies are not executing**: Re-trigger the lifecycle policy job manually and investigate the schedule failure; update CloudWatch alarms for the lifecycle job.
3. **If uncompressed data is accumulating**: Run a compaction job to convert the affected partitions to Parquet and delete the uncompressed originals after verification.
4. **If orphaned temp files are the cause**: Run the standard cleanup job to remove files in `_staging/` or `_temp/` prefixes older than 24 hours.
5. **If growth is legitimate but exceeds quota**: Request a storage quota increase via the infrastructure team and review archival policy thresholds.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer assesses growth rate and identifies cause |
| 15 min | Post findings in #data-incidents |
| 30 min | If write throttling is impacting pipelines: escalate to Data Platform lead |
| 60 min | If storage critical (>90%): escalate to infrastructure team for emergency quota increase |

## Dashboards

- [Data Lake Storage Overview](https://grafana.example.com/d/data-lake-storage) - Usage by bucket, growth rate trends
- [S3 Storage Lens](https://console.aws.amazon.com/s3/storageledger) - Prefix-level storage breakdown
- [Lifecycle Policy Executions](https://grafana.example.com/d/data-lake-lifecycle) - Policy run history and archival rates
- [Pipeline Write Volumes](https://grafana.example.com/d/pipeline-writes) - Bytes written per pipeline per day
