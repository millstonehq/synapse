---
id: MEETING-042
type: meeting
title: Search Relevance Improvement Workshop
status: approved
owner: Principal Engineer
created: '2025-12-28T00:53:23.896Z'
updated: '2026-04-29T13:52:28.796Z'
tags:
  - meeting
  - search-platform
summary: Search Relevance Improvement Workshop
company: SearchPlatform
topic: Search Relevance Improvement Workshop
meeting_date: '2024-11-21T09:19:19.082Z'
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

- **Project**: Search Platform - Relevance Improvement Initiative
- **Topic**: Search Relevance Improvement Workshop
- **Date/Time**: 2024-11-21 09:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead (Search), Data Scientist
- **Attendees (product)**: Product Manager, UX Researcher
- **Context**: Following quarterly quality evaluation showing NDCG@10 of 0.64 against a target of 0.72. Workshop goal: identify the top three actionable improvements.

## Observations by Domain

- **Query Intent Classification**: Analysis of 10,000 recent queries shows 23% are navigational (seeking a specific document) but are being handled by the same full-text ranking model as informational queries — navigational queries need a separate boosting strategy
- **Title Field Weighting**: Explain API analysis of poorly ranked queries shows title field boost at 1.0 is not differentiating title matches from body matches; title relevance is consistently undervalued
- **Synonym Coverage**: Top 20 zero-result queries map to 7 synonym groups that are not in the current dictionary; adding these would reduce zero-result rate from 6.2% to an estimated 4.8%
- **Recency Bias**: Function score recency boost of 3.0x is overwhelming BM25 scores for some queries, surfacing newly indexed but low-quality content above older high-quality content
- **Content Quality Signals**: No document quality signals (e.g., completeness score, view count) are currently used in ranking; product team believes quality signals could significantly improve precision
- **Analyzer Coverage**: German and French content is being analyzed by the English stemmer, producing poor tokenization for those languages

## Key Metrics & Data Points

- **Current NDCG@10**: 0.64 (target: 0.72)
- **Zero-result rate**: 6.2% (target: below 4%)
- **Queries where expected doc is not in top 3**: 31% of annotated query set
- **Recency boost impact**: 18% of queries have a recency-boosted doc at rank 1 that is rated irrelevant by judges
- **Missing synonym groups identified**: 7 high-impact groups covering ~1,200 queries/day

## Preliminary Scorecard Hooks

- Query Intent Handling: 2/5 - No intent classification; navigational and informational queries handled identically
- Field Weight Calibration: 3/5 - Weights functional but suboptimal; title boost requires increase
- Synonym Coverage: 2/5 - Significant gaps for domain vocabulary and product-specific terms
- Recency Boost Calibration: 2/5 - 3.0x multiplier is too aggressive; causing irrelevant content promotion
- Multilingual Support: 1/5 - Non-English content is analyzed incorrectly; major gap for international users

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Recency boost reduction may anger content team expecting fresh content to rank | Medium | Medium | Product Manager | Communicate change with data showing current false positives; reduce to 1.5x not eliminate | 2024-12-15 |
| Synonym additions may introduce false positive matches | Low | Medium | Tech Lead | Test each synonym group against regression query set before adding to production | 2024-12-01 |
| Intent classification model adds query latency overhead | Medium | Low | Principal Engineer | Profile latency impact in staging; ensure P95 stays below 500ms SLO | 2025-01-15 |

## Decisions & Next Steps

### Decisions

- Increase title field boost from 1.0 to 3.0 as the first change (lowest risk, high expected impact)
- Add the 7 identified synonym groups before end of month
- Reduce recency function score multiplier from 3.0x to 1.5x

### Action Items

- Implement title boost increase and run offline benchmark (Tech Lead - 2024-11-30)
- Add 7 synonym groups to synonyms dictionary and reload analyzers (Tech Lead - 2024-11-30)
- Design intent classification prototype for navigational query handling (Principal Engineer - 2024-12-20)

### Follow-ups

- Re-run NDCG evaluation after title boost and synonym changes to measure impact
- Schedule next relevance workshop in 6 weeks to review experiment results
