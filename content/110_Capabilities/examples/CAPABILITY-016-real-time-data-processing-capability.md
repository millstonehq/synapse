---
id: CAPABILITY-016
type: capability
title: Real-Time Data Processing Capability
status: review
owner: Head of Engineering
created: '2024-08-09T05:15:20.993Z'
updated: '2025-04-09T23:39:49.906Z'
tags:
  - capability
  - data-pipeline
summary: Real-Time Data Processing Capability
evidence_links:
  - STANDARD-032
  - PROCESS-034
  - PROCESS-066
example: true
---

## Domain

- Data Engineering
- Platform Engineering
- Operations

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No event streaming infrastructure. Data moved via batch file exports on a daily schedule. No real-time processing capability.
- **Level 1 - Ad hoc**: Kafka cluster exists but is used inconsistently. Some teams publish events; no consumer SLAs or schema contracts. Consumer lag not monitored.
- **Level 2 - Repeatable**: Kafka is used for all high-volume event flows. Consumer lag monitored with basic alerting. No schema enforcement; breaking changes discovered at runtime.
- **Level 3 - Defined** (current): Avro Schema Registry enforces compatibility on all topics. Consumer lag alerting is standardized. At-least-once ingestion guarantee implemented via Aurora checkpoints. ECS micro-batch consumers deliver Tier-1 data within 15 minutes. Airflow orchestrates transformation and quality DAGs on defined schedules.
- **Level 4 - Managed**: Metrics tracked per topic and consumer group (P99 consumer lag, flush latency, dead-letter rate). Automated capacity scaling based on throughput forecasts. Schema registry compatibility violations automatically notify producer teams.
- **Level 5 - Optimizing**: Sub-5-minute freshness for all Tier-1 tables. Automated consumer group rebalancing on broker failure. Zero data loss demonstrated under failure injection testing. Dead-letter rate < 0.01%.

**Gap to Level 4**: Need to implement per-topic capacity forecasting with auto-scaling triggers, and automate producer team notifications on schema registry compatibility rejections.

## Metrics

- End-to-end freshness (Tier-1 topics): Currently P95 = 12 minutes, target < 15 minutes
- End-to-end freshness (standard topics): Currently P95 = 58 minutes, target < 65 minutes
- Consumer lag (peak): Currently max 50,000 messages, target < 100,000 messages
- Dead-letter rate: Currently 0.08% of messages, target < 0.05%
- At-least-once guarantee violations: Currently 0 confirmed in last 90 days, target 0
- Schema registry availability: Currently 99.92%, target > 99.9%

## Evidence Links

- [[STANDARD-032|STANDARD-032]] - Data streaming reliability standards and SLA definitions for the event platform
- [[PROCESS-034|PROCESS-034]] - Kafka topic provisioning and consumer group registration process
- [[PROCESS-066|PROCESS-066]] - Data pipeline capacity planning process ensuring infrastructure scales with event volume growth

## Notes

The organization advanced from Level 2 to Level 3 in Q4 2024 following the Kafka outage incident (Jan 2025), which drove adoption of schema enforcement, standardized alerting, and the Aurora checkpoint guarantee. The micro-batch ingestion path for Tier-1 topics (5-minute flush) launched in Q1 2025 as part of the Real-Time Analytics Pipeline initiative.

Key improvements needed for Level 4:
- Implement per-topic throughput forecasting and auto-scaling alerts (currently manual capacity reviews quarterly)
- Automate Schema Registry compatibility rejection notifications to producer team distribution lists
- Add dead-letter topic monitoring with per-topic rejection rate dashboards
