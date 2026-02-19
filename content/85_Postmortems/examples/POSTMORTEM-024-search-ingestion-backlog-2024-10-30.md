---
id: POSTMORTEM-024
type: postmortem
title: Search Ingestion Backlog 2024-10-30
status: draft
owner: Incident Commander
created: '2024-01-25T04:03:29.247Z'
updated: '2026-07-09T22:24:19.923Z'
tags:
  - postmortem
  - search-platform
summary: Search Ingestion Backlog 2024-10-30
incident_number: INC-455
severity: SEV-1
incident_date: '2024-12-04'
detection_time: '2025-09-16T17:24:43.758Z'
resolution_time: '2024-02-21T22:55:22.733Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-049
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On October 30, 2024, the Search Indexing Pipeline experienced a severe ingestion backlog that grew to over 2 million unprocessed Kafka messages over a 6-hour period. The backlog was caused by the OpenAI embedding API returning elevated error rates (429 rate limit errors) following a platform-wide traffic spike. The embedding workers stopped making progress, and the Kafka consumer lag grew unchecked.

New content published during the 6-hour window was not searchable, impacting content discovery for recently published articles and products. The backlog was cleared over an 8-hour recovery window after rate limits were lifted and throughput was restored. No documents were lost, but search freshness SLO was violated for the day.

## Timeline

- **08:15** - Product team runs a large promotional campaign that drives a 4x spike in content publication rate
- **08:20** - Embedding API call volume exceeds the provisioned rate limit (10,000 calls/min)
- **08:22** - OpenAI embedding API begins returning 429 responses; embedding workers begin retrying with exponential backoff
- **08:35** - Kafka consumer lag crosses 100K messages; `search_indexing_lag_high` alert fires
- **08:37** - On-call engineer acknowledges; identifies consumer lag as the symptom
- **08:45** - On-call identifies embedding worker retry storms as the cause; escalates to tech lead
- **09:00** - Tech lead attempts to increase embedding API rate limit via OpenAI dashboard; limit increase requires support ticket
- **09:15** - Support ticket submitted; ETA for rate limit increase is 2-4 hours
- **11:30** - Kafka consumer lag peaks at 2.1M messages; no new content is searchable
- **14:25** - OpenAI confirms rate limit increased from 10K to 25K calls/min
- **14:30** - Embedding workers clear retry queue and resume normal processing; throughput increases to 3x normal
- **22:40** - Kafka consumer lag fully cleared; all documents indexed; freshness restored

## Impact

- **Duration**: ~6 hours of active backlog (08:22 - 14:30 UTC); full recovery at 22:40 UTC
- **Content freshness**: ~180,000 documents published during the backlog were not searchable for up to 14 hours
- **Query impact**: Existing indexed content was fully searchable; only freshness was affected
- **Revenue impact**: Estimated $18,000 in missed product discovery for newly promoted items
- **SLA impact**: Search freshness SLO (P95 < 30s indexing lag) violated for the full day

## Root Cause Analysis

1. **No rate limit alerting**: The embedding API rate limit was being approached at normal traffic levels. No alert existed for API quota utilization, so the threshold breach during the traffic spike was a surprise.

2. **No keyword-only fallback mode**: The embedding workers had no fallback to index documents without vectors when the embedding API was unavailable. This meant any API disruption stopped all indexing, rather than degrading gracefully to keyword-only search.

## Resolution

1. Submitted OpenAI rate limit increase support ticket
2. Waited for rate limit increase (2-4 hours)
3. Monitored consumer lag reduction after rate limit was lifted
4. Confirmed full backlog clearance at 22:40 UTC

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement keyword-only fallback mode in embedding workers | Search Engineering | P1 | 2024-11-08 | Completed |
| Add embedding API quota utilization alert at 70% of limit | SRE | P1 | 2024-11-08 | Completed |
| Pre-provision embedding API rate limit headroom (2x expected peak) | Search Engineering | P1 | 2024-11-15 | Completed |
| Add Kafka consumer lag circuit breaker that triggers fallback mode automatically | Search Engineering | P2 | 2024-11-30 | In Progress |

## Lessons Learned

- **What went well**: No documents were lost; all content was eventually indexed. The support ticket process worked and rate limits were increased within the promised SLA.
- **What went poorly**: Six hours elapsed before the rate limit was identified as the root cause. The lack of a fallback mode turned a service degradation into a full search freshness outage.
- **What was lucky**: The embedding API rate limit was eventually increased within the day. If the increase had taken longer, the backlog recovery would have stretched into the next day.
