---
id: MEETING-043
type: meeting
title: Elasticsearch Upgrade Planning Session
status: accepted
owner: Product Manager
created: '2025-03-06T20:33:58.502Z'
updated: '2026-02-11T12:34:52.670Z'
tags:
  - meeting
  - search-platform
summary: Elasticsearch Upgrade Planning Session
company: SearchPlatform
topic: Elasticsearch Upgrade Planning Session
meeting_date: '2025-06-15T21:51:24.925Z'
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

- **Project**: Search Platform - Elasticsearch 7 to 8 Upgrade
- **Topic**: Elasticsearch Upgrade Planning Session
- **Date/Time**: 2025-06-15 02:00 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead (Platform), DevOps Lead, SRE Lead
- **Attendees (product)**: Product Manager
- **Context**: Elasticsearch 7.x reaches end-of-life in August 2025. Planning the migration timeline to ES8 to maintain security patch support and access to new features (ESQL, improved kNN search).

## Observations by Domain

- **Breaking Changes**: ES8 removes several deprecated REST APIs used in the ingestion pipeline; `_type` field removal requires mapping migration for 3 indexes that still use type-based routing
- **Security**: ES8 enables security (TLS + authentication) by default; current cluster runs with security disabled; enabling security requires certificate provisioning and client credential updates across all services
- **Query DSL Changes**: The `match_phrase_prefix` query behavior changed in ES8; the ranking team needs to audit all query templates for affected patterns
- **JVM Requirements**: ES8 requires JDK 17+; current cluster runs JDK 11; node image updates and JVM flag migration are required
- **Rolling Upgrade Path**: ES supports rolling upgrades from 7.17 to 8.x; current cluster is at 7.14 and must first be upgraded to 7.17 before attempting the ES8 migration
- **Snapshot Compatibility**: ES8 cannot restore snapshots created by versions older than 7.x; snapshots are compatible for the planned upgrade path

## Key Metrics & Data Points

- **Current Elasticsearch version**: 7.14.2
- **Required intermediate version**: 7.17.x (prerequisite for ES8 rolling upgrade)
- **Estimated migration duration**: 3 weeks (7.14 to 7.17: 1 week, 7.17 to 8.x: 2 weeks)
- **APIs to migrate in ingestion pipeline**: 4 deprecated API calls identified in code audit
- **Indexes requiring type-field migration**: 3 indexes with `_type`-based mapping patterns
- **Services requiring security credential updates**: 7 services that query Elasticsearch directly

## Preliminary Scorecard Hooks

- Migration Readiness: 2/5 - Cluster is 3 minor versions behind the required intermediate; mapping and API changes create non-trivial migration scope
- Security Posture Post-Upgrade: 5/5 - ES8 security-by-default will be a significant improvement; current no-auth cluster is a known security gap
- Testing Coverage for Upgrade: 3/5 - Staging environment exists but does not mirror production index size; performance testing will need a separate data load
- Rollback Planning: 2/5 - Rolling upgrade can be paused but not rolled back once more than half the nodes are upgraded; blue-green cluster strategy is preferred

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Ingestion pipeline breaks due to deprecated API removal | High | Certain | Tech Lead | Complete API migration before upgrade; test against ES8 in staging | 2025-07-15 |
| Security enablement breaks services missing credentials | High | High | SRE Lead | Provision credentials for all 7 services and test connectivity in staging before production rollout | 2025-07-20 |
| JVM flag incompatibilities causing OOM on node restart | Medium | Medium | DevOps Lead | Test updated JVM flags in staging under production-representative load | 2025-07-10 |

## Decisions & Next Steps

### Decisions

- Use a blue-green cluster strategy for the ES8 upgrade rather than rolling upgrade to allow safe rollback
- Complete the 7.14 to 7.17 intermediate upgrade before end of July 2025
- Security enablement will be part of the ES8 upgrade, not a separate step

### Action Items

- Audit all ingestion pipeline code for deprecated ES8 API usage (Tech Lead - 2025-06-30)
- Provision TLS certificates and client credentials for the new ES8 cluster (SRE Lead - 2025-07-10)
- Upgrade staging cluster to ES8 and run full regression test suite (DevOps Lead - 2025-07-20)

### Follow-ups

- Weekly upgrade progress syncs starting July 1st
- Go/no-go review for production upgrade scheduled for August 1st
