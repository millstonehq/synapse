---
id: RUNBOOK-005
type: runbook
title: Payment Database Replication Lag Runbook
status: approved
owner: On-Call Engineer
created: '2025-11-10T14:42:28.550Z'
updated: '2026-01-08T02:17:31.888Z'
tags:
  - runbook
  - payment-processing
summary: Payment Database Replication Lag Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `PaymentDBReplicationLagHigh` — Aurora replica lag exceeds 30 seconds sustained for 5 minutes
- `PaymentDBReplicationLagCritical` — Aurora replica lag exceeds 120 seconds
- `PaymentDBReadReplicaUnhealthy` — read replica returns health check errors or is unreachable
- `PaymentDBReplicationStopped` — replication has stopped completely on the standby replica

## Diagnosis Steps

1. **Check Aurora replica lag metric** - Open the RDS console or CloudWatch and review the `AuroraReplicaLag` metric; note the lag value and the trend (increasing vs. stabilizing).
2. **Identify write workload spikes** - Check the primary database write IOPS and transaction throughput; a sudden write spike (e.g., batch reconciliation job, bulk update) causes temporary replication lag.
3. **Check replica instance health** - Confirm the replica instance is running and responding to connection attempts; a stopped or rebooting replica is the most common cause of sudden replication stop.
4. **Review long-running transactions** - Check for long-running transactions on the primary that block replication apply on the replica; query `pg_stat_activity` for transactions open longer than 5 minutes.
5. **Assess network throughput** - For cross-AZ replicas, check VPC network throughput between primary and replica AZs; network saturation can cause replication lag during high-write periods.

## Remediation Steps

1. **If write spike caused by a batch job**: Throttle or pause the batch job (e.g., reconciliation, bulk backfill) until replication lag returns below 10 seconds; then resume at reduced rate.
2. **If long-running transaction blocking replication**: Identify and kill the blocking transaction with DBA approval; confirm replication resumes after the blocker is cleared.
3. **If replica instance is stopped or unhealthy**: Restart the replica instance from the RDS console; replication will resume from the binary log position; monitor lag recovery.
4. **If replication lag approaches 120 seconds**: Switch read traffic back to the primary database temporarily to prevent stale reads; update the payment service read-endpoint configuration.
5. **If replication is stopped and lag is non-recoverable**: Initiate the payment database failover SOP if the primary is also affected; otherwise rebuild the replica from the primary.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks replica lag metric and write workload |
| 15 min | If lag exceeds 60 seconds and is not recovering, notify Engineering Manager and on-call DBA |
| 30 min | DBA and on-call engineer assess failover necessity; Engineering Manager informed of decision |
| 60 min | If replication stopped and primary at risk, Director of Engineering authorizes database failover |

## Dashboards

- [Payment Database Replication](https://grafana.example.com/d/payment-db-replication) - Replica lag, write IOPS, and replication throughput
- [Payment Database Overview](https://grafana.example.com/d/payment-db-overview) - Connection count, query latency, and storage metrics
- [Aurora Cluster Health](https://grafana.example.com/d/aurora-cluster) - Cluster instance status and failover history
