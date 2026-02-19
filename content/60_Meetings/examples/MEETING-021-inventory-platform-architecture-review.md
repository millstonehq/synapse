---
id: MEETING-021
type: meeting
title: Inventory Platform Architecture Review
status: approved
owner: Product Manager
created: '2025-09-29T00:59:31.142Z'
updated: '2025-11-27T10:06:11.114Z'
tags:
  - meeting
  - inventory-management
summary: Inventory Platform Architecture Review
company: InventoryManagement
topic: Inventory Platform Architecture Review
meeting_date: '2025-02-02T03:34:20.830Z'
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

- **Project**: Inventory Platform Modernization
- **Topic**: Inventory Platform Architecture Review
- **Date/Time**: 2025-02-02 9:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Inventory Platform Engineer
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Quarterly architecture review to assess current platform health, identify scaling bottlenecks, and prioritize the roadmap for the next quarter.

## Observations by Domain

- **Event Pipeline**: Kafka consumer lag has been consistently elevated during nightly sync windows, indicating the event processor is under-provisioned for batch workloads
- **Database Layer**: ClickHouse query performance is degrading as the stock_movements table grows; partitioning strategy needs revisiting for tables over 500M rows
- **API Layer**: Inventory API P95 latency is within SLA but cache hit rate has declined since the last deployment, suggesting a cache configuration regression
- **Warehouse Integrations**: Three warehouse adapters are running on an older event format version; migration to the current schema version has been delayed for two quarters
- **Observability**: Alert coverage is good for infrastructure issues but there are gaps in business metric alerting (e.g., no alert for sustained data freshness violations)

## Key Metrics & Data Points

- **Kafka consumer lag (peak)**: 85,000 messages during nightly sync (threshold: 50,000)
- **ClickHouse stock_movements rows**: 620M (query performance degrades above 500M without partition pruning)
- **Inventory API cache hit rate**: 71% (target: 85%; was 88% before last deployment)
- **Warehouse adapters on legacy schema**: 3 of 11 (target: 0)
- **API P95 latency**: 320ms (SLA: 500ms)

## Preliminary Scorecard Hooks

- Event Pipeline: 3/5 - Functional but consumer lag during batch windows is a reliability risk
- Database Layer: 3/5 - Performance concerns emerging at scale; partitioning work is overdue
- API Layer: 4/5 - Within SLA but cache regression needs investigation
- Warehouse Integrations: 3/5 - Legacy schema adapters are a maintenance and compatibility risk
- Observability: 3/5 - Infrastructure coverage good; business metric alerting gaps remain

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Consumer lag during nightly sync breaches data freshness SLA | High | Medium | Tech Lead | Scale event processor during batch windows; implement auto-scaling based on lag | 2025-03-01 |
| ClickHouse query degradation affecting analytics SLAs | High | High | Principal Engineer | Implement partition pruning by warehouse_id + month; archive movements older than 2 years | 2025-02-28 |
| Legacy schema adapters break on next event format version change | Medium | High | Inventory Platform Engineer | Migrate 3 legacy adapters to current schema version | 2025-03-15 |
| Cache regression causing elevated database read load | Medium | Low | Tech Lead | Investigate cache configuration change in last deployment; restore hit rate to 85%+ | 2025-02-14 |

## Decisions & Next Steps

### Decisions

- ClickHouse partitioning work is promoted to P1 for Q1; blocking any further schema changes until complete
- Legacy schema adapter migration is assigned to the Inventory Platform Engineer with a hard deadline of March 15
- Auto-scaling for the event processor during batch windows is approved; Tech Lead to implement before next nightly sync window review

### Action Items

- Investigate cache hit rate regression: compare cache config before and after last deployment (Tech Lead - 2025-02-07)
- Design ClickHouse partition scheme for stock_movements and propose archive policy (Principal Engineer - 2025-02-14)
- Migrate first legacy warehouse adapter to current schema as a pilot (Inventory Platform Engineer - 2025-02-21)
- Write alerting spec for business metric gaps identified today (Product Manager - 2025-02-14)

### Follow-ups

- Next architecture review: 2025-05-02
- Check-in on cache hit rate at next weekly sync
- ClickHouse partition implementation review before merging to production
