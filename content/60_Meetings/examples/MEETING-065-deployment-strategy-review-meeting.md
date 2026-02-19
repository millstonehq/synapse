---
id: MEETING-065
type: meeting
title: Deployment Strategy Review Meeting
status: approved
owner: Engineering Manager
created: '2024-06-25T23:18:48.845Z'
updated: '2026-10-07T02:27:49.643Z'
tags:
  - meeting
  - ci-cd-platform
summary: Deployment Strategy Review Meeting
company: CI/CDPlatform
topic: Deployment Strategy Review Meeting
meeting_date: '2025-05-24T17:53:57.807Z'
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

- **Project**: Deployment Strategy Evolution
- **Topic**: Review of current deployment strategies (rolling, blue-green, canary) and alignment on which patterns each service class should adopt
- **Date/Time**: 2025-05-24 17:53 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Post-incident review from Q1 found that 60% of production incidents were deployment-related; standardizing on progressive delivery strategies is a key mitigation

## Observations by Domain

- **Rolling Deployments**: Currently the default strategy for all services; provides no traffic control during rollout and makes rollback slow for large fleets
- **Blue-Green Adoption**: Four services piloted blue-green in Q1 with positive results; rollback time reduced from 8 minutes average to under 1 minute; however, requires 2x resource headroom during deployment
- **Canary Deployments**: Not yet in production use; ArgoCD Rollouts is installed but only one team has experimented with it in staging
- **Database Migration Coupling**: The largest source of deployment risk is database migrations coupled with application deployments; teams do not consistently follow expand-contract pattern
- **Deployment Windows**: No formal deployment windows exist; teams deploy at any time, making it difficult to correlate metric changes with specific deployments

## Key Metrics & Data Points

- **Deployment-related incident rate**: 4.2 incidents per 100 deployments across all services
- **Blue-green pilot rollback time**: 48 seconds average (vs 8 minutes for rolling)
- **Services with backward-incompatible DB migrations in last 6 months**: 7 services
- **Average deployment frequency per service**: 4.3 deployments per week
- **Time to detect deployment-caused regression**: 22 minutes average (target: under 5 minutes)

## Preliminary Scorecard Hooks

- Deployment Safety: 2/5 - Rolling deployments offer minimal blast radius control; incident rate is high
- Rollback Speed: 2/5 - Rolling rollback is too slow; blue-green pilot demonstrates viable path
- Database Migration Safety: 1/5 - Backward incompatibility in 7 services represents critical unmitigated risk
- Deployment Observability: 3/5 - Metrics exist but detection time is too high at 22 minutes
- Progressive Delivery Maturity: 2/5 - Blue-green piloted; canary deployments not yet in production use

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Customer-facing incident caused by backward-incompatible DB migration | High | High | Principal Engineer | Enforce expand-contract migration pattern via pre-deploy checklist | 2025-07-01 |
| Blue-green rollout doubles resource cost for all services | Medium | High | Tech Lead | Calculate per-service cost impact; limit blue-green to Tier 1 services initially | 2025-06-15 |
| Canary traffic splitting misconfigured causing data inconsistency | High | Low | Principal Engineer | Require QA Lead sign-off on canary configuration before each use | 2025-08-01 |

## Decisions & Next Steps

### Decisions
- Mandate blue-green deployments for all Tier 1 (customer-facing, revenue-impacting) services by end of Q3 2025
- Require all database migrations to follow expand-contract pattern with QA Lead sign-off; no backward-incompatible migrations without documented rollback SQL
- Establish formal deployment windows (09:00–16:00 weekdays) for Tier 1 services; emergency exceptions require manager approval

### Action Items
- Tech Lead to classify all services into Tier 1/2/3 and estimate resource cost of blue-green for Tier 1 services by 2025-06-15
- Principal Engineer to write the expand-contract migration guide and create a pre-deploy checklist template
- QA Lead to define acceptance criteria for Tier 1 blue-green migration verification

### Follow-ups
- Review deployment-related incident rate at next quarterly review to measure strategy impact
- Revisit canary deployment adoption roadmap once blue-green is fully rolled out
