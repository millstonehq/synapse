---
id: MEETING-044
type: meeting
title: Search Team Sprint Planning
status: approved
owner: Engineering Manager
created: '2024-02-27T06:10:47.164Z'
updated: '2025-10-05T11:57:41.931Z'
tags:
  - meeting
  - search-platform
summary: Search Team Sprint Planning
company: SearchPlatform
topic: Search Team Sprint Planning
meeting_date: '2025-05-20T14:53:49.840Z'
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

- **Project**: Search Platform - Sprint 24
- **Topic**: Search Team Sprint Planning
- **Date/Time**: 2025-05-20 02:00 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Search Engineer (x2)
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Sprint 24 planning session. Previous sprint velocity: 38 story points. Capacity this sprint: 40 points (one engineer at 50% capacity due to on-call rotation).

## Observations by Domain

- **Relevance Work**: Title boost experiment from Sprint 23 reached statistical significance with +1.8 NDCG@10 improvement; ready for full rollout this sprint
- **Infrastructure**: Ingestion pipeline lag alerting was completed in Sprint 23 and is functioning in production
- **Tech Debt**: The synonym dictionary management is still a manual file edit process; automation is needed before the dictionary grows further
- **New Feature**: Product team is requesting vector search (kNN) for semantic similarity results by Q3; feasibility spike needs to be scoped this sprint
- **Quality**: Zero-result rate dropped from 6.2% to 5.1% after synonym additions in Sprint 23; still above the 4% target
- **On-Call**: Two incidents in Sprint 23 related to shard rebalancing during scaling operation; SOP was unclear and took 40 minutes to resolve

## Key Metrics & Data Points

- **Current NDCG@10**: 0.68 (up from 0.64 two sprints ago; target: 0.72)
- **Zero-result rate**: 5.1% (target: 4.0%)
- **Cluster heap peak**: 79% (improved from 82% after node addition)
- **Sprint 23 velocity**: 38 points
- **Sprint 24 capacity**: 40 points
- **Open P1 bugs**: 1 (synonym reload occasionally drops a small batch of active queries)

## Preliminary Scorecard Hooks

- Relevance Progress: 3/5 - Measurable improvement this sprint but still 4 NDCG points below target
- Infrastructure Stability: 4/5 - Alerting improved; shard rebalancing SOP gap needs documentation update
- Feature Velocity: 3/5 - On track for Q2 commitments; kNN feasibility spike is risk item for Q3
- Team Health: 4/5 - Velocity consistent; one engineer partial capacity due to on-call is manageable

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| kNN feasibility spike takes longer than 1 sprint to scope | Medium | Medium | Principal Engineer | Time-box to 3 story points; escalate if blocked on ES version compatibility | 2025-06-03 |
| P1 bug in synonym reload could affect query results | High | Low | Tech Lead | Fix prioritized as Sprint 24 day-1 work item; root cause identified | 2025-05-22 |

## Decisions & Next Steps

### Decisions

- Roll out title boost ranking change to 100% of traffic at sprint start (A/B test already concluded)
- Fix the synonym reload P1 bug before any other work begins
- Allocate 3 story points to the kNN feasibility spike

### Action Items

- Promote title boost to 100% traffic and update ranking config registry (Search Engineer - 2025-05-21)
- Fix synonym reload race condition bug (Tech Lead - 2025-05-22)
- Update the Elasticsearch shard relocation SOP with clearer diagnosis steps (Principal Engineer - 2025-05-28)

### Follow-ups

- Mid-sprint check-in on kNN spike progress on 2025-05-28
- Sprint review and retrospective on 2025-06-03
