---
id: MEETING-052
type: meeting
title: Kafka Cluster Migration Planning
status: approved
owner: Product Manager
created: '2025-08-11T02:59:53.565Z'
updated: '2025-07-15T15:17:15.861Z'
tags:
  - meeting
  - data-pipeline
summary: Kafka Cluster Migration Planning
company: DataPipeline
topic: Kafka Cluster Migration Planning
meeting_date: '2026-04-07T16:57:06.403Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Data Platform Infrastructure
- **Topic**: Kafka Cluster Migration Planning
- **Date/Time**: 2026-04-07 2:00 PM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Infrastructure Lead
- **Attendees (product)**: Engineering Manager, QA Lead
- **Context**: Planning session for migrating the Kafka cluster from self-managed Kubernetes deployment to Confluent Cloud.

## Observations by Domain

- **Current State**: Kafka 2.8 running on-prem Kubernetes; 22 topics, 3 consumer groups, ~15M messages/day; cluster management is high overhead for the team.
- **Migration Target**: Confluent Cloud with managed connectors; removes broker management burden and provides built-in monitoring.
- **Schema Registry**: Confluent Cloud includes managed Schema Registry; migration requires re-registering all 22 existing schemas.
- **Consumer Impact**: All 12 consumer groups require bootstrap server and security config updates; no consumer code changes expected.
- **Downtime Risk**: If migrated with dual-write and offset sync, expected zero-downtime cutover; requires 1-2 week parallel operation window.
- **Cost**: Confluent Cloud estimated at 1.4x current self-managed infrastructure cost; offset by reduced engineering hours for cluster maintenance.

## Key Metrics & Data Points

- **Current throughput**: 15M messages/day across 22 topics
- **Consumer groups**: 12 active groups
- **Average consumer lag (steady state)**: <500 messages
- **Cluster management overhead**: ~8 engineer-hours/month
- **Estimated migration duration**: 3 weeks with parallel operation
- **Schema count requiring re-registration**: 22

## Preliminary Scorecard Hooks

- Migration readiness: 3/5 - Plan solid but consumer config update scope not fully inventoried
- Risk posture: 4/5 - Dual-write approach reduces cutover risk significantly
- Schema migration: 3/5 - Re-registration feasible but needs scripted automation
- Team readiness: 3/5 - Confluent Cloud experience limited; training needed before cutover

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Consumer config update misses a service | High | Medium | Tech Lead | Inventory all consumer applications before migration start | 2026-04-14 |
| Schema re-registration breaks compatibility | High | Low | Principal Engineer | Script and test full schema re-registration in staging first | 2026-04-21 |
| Message loss during cutover | High | Low | Infrastructure Lead | Implement dual-write with offset verification before cutover | 2026-04-28 |
| Confluent cost overrun due to retention settings | Medium | Medium | Engineering Manager | Audit and align retention settings before migration | 2026-04-14 |

## Decisions & Next Steps

### Decisions

- Confluent Cloud is the approved migration target; self-managed Kafka will be decommissioned post-migration
- Dual-write with parallel operation window is the required migration approach; no big-bang cutover
- Schema re-registration must be scripted and tested in staging before production migration

### Action Items

- Inventory all consumer applications and document config changes required (Tech Lead - 2026-04-14)
- Build schema re-registration script and test in staging (Principal Engineer - 2026-04-21)
- Draft detailed migration runbook with rollback steps (Infrastructure Lead - 2026-04-28)

### Follow-ups

- Weekly migration sync during the active migration period
- Post-migration review 2 weeks after cutover to confirm stability
