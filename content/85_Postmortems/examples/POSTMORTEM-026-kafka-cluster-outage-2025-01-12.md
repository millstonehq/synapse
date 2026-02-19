---
id: POSTMORTEM-026
type: postmortem
title: Kafka Cluster Outage 2025-01-12
status: review
owner: On-Call Engineer
created: '2025-03-29T05:50:28.960Z'
updated: '2025-09-14T20:08:23.962Z'
tags:
  - postmortem
  - data-pipeline
summary: Kafka Cluster Outage 2025-01-12
incident_number: INC-547
severity: SEV-4
incident_date: '2025-01-05'
detection_time: '2025-05-14T20:13:11.522Z'
resolution_time: '2025-01-29T04:34:27.994Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-053
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 12, 2025, the Kafka cluster serving the data pipeline experienced a 4-hour degraded throughput event caused by a leadership election storm. A rolling broker restart initiated by the infrastructure team triggered simultaneous partition leadership elections across multiple brokers. The cluster struggled to rebalance, and throughput dropped to 20% of normal capacity during the storm. No messages were lost due to replication factor 3, but consumer groups fell 36 hours behind by the time the storm stabilized.

The incident was detected by automated consumer lag alerting at 09:14 UTC and the cluster returned to normal throughput by 13:22 UTC. Consumer lag drainage took an additional 36 hours due to the backlog depth.

## Timeline

- **08:50** - Infrastructure team begins rolling broker restart to apply OS patches (not communicated to data engineering on-call)
- **09:05** - Partition leadership elections begin as brokers restart; election timeout cascade begins
- **09:14** - `kafka_consumer_lag_high` alert fires for 4 consumer groups simultaneously. On-call acknowledges.
- **09:20** - On-call investigates; sees under-replicated partitions increasing across 3 brokers
- **09:35** - Infrastructure team notified; rolling restart paused at broker 4 of 6
- **09:50** - Tech lead joins; identifies leadership election storm from JMX metrics
- **10:15** - Preferred replica election forced via `kafka-preferred-replicas-election.sh` for top 50 most impacted topics
- **11:30** - Throughput recovering but election storm still active on 2 brokers
- **12:45** - Remaining 2 brokers restarted individually with 15-minute cooldown between restarts
- **13:22** - Cluster throughput returns to 95% of baseline; election storm resolved
- **Jan 13, 01:00** - Consumer lag fully drained; all groups at baseline

## Impact

- **Duration**: 4 hours of degraded throughput (09:14 - 13:22 UTC)
- **Consumer lag peak**: 2.1 million messages across all consumer groups
- **Lag drainage time**: 36 hours to fully drain backlog
- **Downstream analytics impact**: Tier-1 datasets stale for up to 12 hours; BI dashboards showed outdated data
- **SLA impact**: January pipeline availability dropped to 99.85% (below 99.9% target)
- **Data loss**: Zero — replication factor 3 with min.insync.replicas=2 ensured no message loss

## Root Cause Analysis

1. **Missing change communication process**: The infrastructure team's rolling broker restart was not communicated to data engineering. There was no pre-restart coordination step requiring notification of affected teams before production Kafka changes.

2. **Aggressive election timeout configuration**: The `leader.imbalance.check.interval.seconds` and `unclean.leader.election.enable=true` setting (at the time) allowed concurrent leadership elections when multiple brokers restarted in rapid succession, creating a self-reinforcing election storm.

## Resolution

1. Paused rolling restart at broker 4 to stop adding to the election storm
2. Ran preferred replica election on the 50 most-impacted topics to redistribute leadership
3. Completed remaining broker restarts with 15-minute cooldowns between each
4. Monitored consumer group lag drainage over 36 hours to confirm full recovery

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Set `unclean.leader.election.enable=false` on all brokers | Infra | P1 | 2025-01-15 | Completed |
| Add Kafka maintenance to change communication process | Infra + Data Eng | P1 | 2025-01-20 | Completed |
| Create runbook for broker rolling restart with cooldown procedure | On-call | P2 | 2025-01-31 | Completed |
| Add `under_replicated_partitions > 0` alert to on-call rotation | SRE | P2 | 2025-01-25 | Completed |

## Lessons Learned

- **What went well**: Replication factor 3 with min.insync.replicas=2 meant zero data loss despite 4 hours of degradation. Consumer lag alerting fired within 9 minutes of throughput drop.
- **What went poorly**: No change communication between infrastructure and data engineering prior to broker restart. On-call spent 20 minutes diagnosing before root cause (external restart) was identified.
- **What was lucky**: The restart was paused at broker 4 of 6; completing the restart on all 6 simultaneously would have been far worse.
