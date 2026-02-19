---
id: RUNBOOK-076
type: runbook
title: Data Pipeline Checkpoint Recovery Runbook
status: review
owner: On-Call Engineer
created: '2025-10-30T12:45:04.511Z'
updated: '2026-12-26T02:53:53.764Z'
tags:
  - runbook
  - data-pipeline
summary: Data Pipeline Checkpoint Recovery Runbook
example: true
---

## Service

- **System**: [[SYSTEM-030|Data Lake Ingestion Service]]
- **Owner team**: Data Engineering
- **On-call rotation**: PagerDuty schedule "data-engineering-oncall"
- **Slack channel**: #data-pipeline-incidents
- **Runtime**: ECS Fargate / Java 21 / Apache Iceberg / Aurora PostgreSQL

## Alerts

- `kafka_offset_continuity_gap` - Kafka offset gap > 1,000 offsets detected between checkpoint and current broker offset
- `iceberg_checkpoint_age_high` - No successful Iceberg checkpoint committed in > 10 minutes
- `data_quality_completeness_breach` - Data quality completeness rule breach after recovery suggesting records were skipped
- `ecs_ingestion_task_crash` - ECS ingestion task terminated unexpectedly (exit code non-zero)
- `consumer_lag_high_post_restart` - Consumer lag > 50,000 messages 5 minutes after ECS task restart

## Diagnosis Steps

1. **Confirm checkpoint gap exists** - Query the Aurora checkpoint table: `SELECT consumer_group, topic, partition, committed_offset, committed_at FROM consumer_checkpoints WHERE committed_at < NOW() - INTERVAL '15 minutes' ORDER BY committed_at ASC;`. If rows are older than 15 minutes, the checkpoint has not been updated — the task may be crashed or stalled.
2. **Compare checkpoint offset to Kafka broker offset** - Using the Kafka consumer group CLI: `kafka-consumer-groups.sh --bootstrap-server $KAFKA_BROKERS --describe --group $CONSUMER_GROUP`. Compare `CURRENT-OFFSET` in Aurora to `LOG-END-OFFSET` from Kafka. If the Aurora checkpoint is ahead of where Iceberg has confirmed data, a gap exists.
3. **Check Iceberg table watermark** - Query via Trino: `SELECT MAX(event_time) FROM data_lake_prod.raw.<table> WHERE ingestion_date = CURRENT_DATE;`. Compare to the expected ingestion window based on the Aurora checkpoint timestamp.
4. **Identify the gap window** - If a gap is confirmed, determine the time range by comparing: (a) the last successful Aurora checkpoint timestamp and (b) the Iceberg table's most recent `MAX(event_time)`. The gap window is between these two values.
5. **Check ECS task logs for crash context** - In CloudWatch Logs (`/ecs/data-lake-ingestion`), search for `ERROR` and `FATAL` entries around the checkpoint gap window. Look for `IcebergWriteException`, `CheckpointCommitFailed`, or JVM OOM errors.
6. **Verify current ECS task health** - In the ECS console, confirm the ingestion task is running and healthy. If the task is in STOPPED or PENDING state, recovery cannot proceed until a task is running and consuming from the correct offset.

## Remediation Steps

1. **If the current task is running from the wrong offset (gap confirmed)**: Stop the current ECS task: `aws ecs stop-task --cluster data-pipeline-prod --task $TASK_ARN`. Wait for the task to stop, then manually correct the Aurora checkpoint: `UPDATE consumer_checkpoints SET committed_offset = $CORRECT_OFFSET, committed_at = NOW() WHERE consumer_group = '$GROUP' AND topic = '$TOPIC' AND partition = $PARTITION;`. Restart the ECS task. Verify new commits appear in Aurora within 5 minutes.
2. **If the gap is confirmed and Kafka retention covers the missing window**: Launch a manual replay consumer targeting the gap offset range. The replay consumer is deployed as a one-off ECS task using the `data-lake-ingestion-replay` task definition with the environment variables `REPLAY_START_OFFSET` and `REPLAY_END_OFFSET` set to the gap boundaries. Monitor the replay consumer via CloudWatch until all offsets in the gap are committed.
3. **If the gap is outside Kafka retention (> 7 days)**: Escalate immediately to the Data Engineering tech lead and incident commander. Permanent data loss has occurred. Begin impact assessment: which Iceberg tables are affected, what business processes consume them, and whether any upstream source systems retain the data for an alternative recovery path.
4. **If the ECS task is crashing on restart**: Check CloudWatch Logs for the crash reason. If an OOM kill, increase the ECS task memory configuration in Terraform and redeploy. If an `IcebergWriteException`, the Iceberg table may be locked by a concurrent compaction job — wait for the compaction to complete before restarting.
5. **After recovery, verify data completeness**: Run the data quality completeness rule manually against the recovered table: trigger the quality Lambda with the specific rule ID. Confirm the completeness rule passes before closing the incident.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post initial assessment in #data-pipeline-incidents with gap window estimate |
| 15 min | If gap confirmed and > 100,000 records: page Data Engineering tech lead |
| 30 min | If replay consumer not launched or gap > 7-day Kafka retention: page Engineering Manager |
| 60 min | If permanent data loss confirmed: initiate major incident process |

**Who to escalate to:**
- Data Engineering tech lead: PagerDuty schedule "data-eng-leads"
- Infrastructure issues (ECS, Aurora): PagerDuty schedule "infra-oncall"
- Kafka broker issues: PagerDuty schedule "platform-oncall"

## Dashboards

- [Data Lake Ingestion Overview](https://grafana.example.com/d/data-lake-ingestion) - Consumer lag, flush latency, checkpoint age
- [Kafka Consumer Groups](https://grafana.example.com/d/kafka-consumer-groups) - Per-topic consumer lag and offset comparison
- [Aurora Checkpoint Table](https://grafana.example.com/d/aurora-checkpoints) - Last checkpoint time per consumer group
- [Iceberg Table Watermarks](https://grafana.example.com/d/iceberg-watermarks) - MAX(event_time) per table vs. expected watermark
- [ECS Data Pipeline Tasks](https://grafana.example.com/d/ecs-data-pipeline) - Task health, restart count, memory usage
