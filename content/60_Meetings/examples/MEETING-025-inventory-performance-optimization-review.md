---
id: MEETING-025
type: meeting
title: Inventory Performance Optimization Review
status: approved
owner: Engineering Manager
created: '2024-12-29T16:45:13.742Z'
updated: '2025-09-23T21:12:14.766Z'
tags:
  - meeting
  - inventory-management
summary: Inventory Performance Optimization Review
company: InventoryManagement
topic: Inventory Performance Optimization Review
meeting_date: '2025-03-10T23:15:11.546Z'
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

- **Project**: Inventory Platform Performance
- **Topic**: Inventory Performance Optimization Review
- **Date/Time**: 2025-03-10 5:15 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Platform Engineer
- **Attendees (product)**: Engineering Manager, Product Manager
- **Context**: Post-incident performance review following P95 latency SLA breach on the inventory API. New enterprise customer onboarding tripled query volume; several optimization opportunities were identified during the incident investigation.

## Observations by Domain

- **API Latency**: `/v1/inventory` P95 latency reached 820ms during peak (SLA: 500ms); profiling identified read replica connection wait as the primary bottleneck, not query execution time
- **Read Replica Load Balancing**: A load balancing bug introduced in last month's deployment causes 80% of reads to route to a single replica instead of distributing across both
- **Cache Warm Coverage**: Cache miss rate increased to 34% when the new enterprise customer began querying warehouses not in the warm set; cold misses bypass cache entirely and hit the database
- **HPA Ceiling**: Inventory API reached HPA maximum of 12 pods during the peak; pod count ceiling prevented further horizontal scaling
- **ClickHouse Analytics**: Analytics performance is acceptable at current volume; cross-region queries will need partition optimization for Q3 expansion

## Key Metrics & Data Points

- **API P95 latency (peak)**: 820ms (SLA: 500ms; target: 280ms)
- **Read replica pool utilization**: 95% (target: <70%)
- **Cache miss rate**: 34% (was 15% pre-enterprise customer; target: <20%)
- **HPA pod count at peak**: 12 of 12 max
- **Enterprise customer incremental query volume**: +180k requests/hour

## Preliminary Scorecard Hooks

- API Latency: 1/5 - SLA breach; read replica load balancing bug is root cause
- Read Replica Health: 1/5 - 80% traffic to single replica is unsustainable
- Cache Efficiency: 2/5 - Enterprise customer cold cache misses require pre-warming strategy
- Horizontal Scaling: 2/5 - HPA max cap prevents scaling; needs increase
- Analytics Performance: 4/5 - Within targets; future work needed for Q3 expansion

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Read replica single-point overload cascades to primary | Critical | High | Principal Engineer | Fix load balancing bug immediately; ship as emergency change | 2025-03-11 |
| Cache cold misses for new enterprise customers will recur | Medium | High | Tech Lead | Implement cache pre-warming job triggered on enterprise customer onboarding | 2025-04-01 |
| HPA max cap prevents scaling during traffic spikes | Medium | High | Platform Engineer | Raise HPA max to 20; validate auto-scaling thresholds | 2025-03-17 |
| Third read replica not yet provisioned for redundancy | Medium | Medium | Platform Engineer | Provision third read replica with PgBouncer connection pooler | 2025-04-15 |

## Decisions & Next Steps

### Decisions

- Read replica load balancing fix is an emergency change; ship today without waiting for normal release cycle
- HPA max raised to 20 immediately as an interim scaling measure
- Cache pre-warming is approved for Q2 work; Tech Lead to own design

### Action Items

- Fix read replica load balancing configuration and deploy (Principal Engineer - 2025-03-11)
- Raise HPA max to 20 and update auto-scaling thresholds (Platform Engineer - 2025-03-12)
- Design cache pre-warming job for enterprise customer onboarding (Tech Lead - 2025-03-24)
- Provision third read replica and evaluate PgBouncer (Platform Engineer - 2025-04-15)

### Follow-ups

- P95 latency check 24 hours after load balancing fix
- Performance review at next weekly sync to confirm recovery
- Cache pre-warming design review: 2025-03-27
