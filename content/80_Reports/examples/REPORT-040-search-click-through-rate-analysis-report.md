---
id: REPORT-040
type: report
title: Search Click-Through Rate Analysis Report
status: approved
owner: Search Tech Lead
created: '2024-08-30T21:42:55.547Z'
updated: '2026-10-09T07:59:08.804Z'
tags:
  - report
  - search-platform
summary: Search Click-Through Rate Analysis Report
company: SearchPlatform
report_month: 2025-07
report_type: portfolio
overall_health: poor
confidence: low
active_initiatives_count: 7
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall CTR | > 38% | 33.1% | Below target |
| Position-1 CTR | > 55% | 49.8% | Below target |
| Position-2 CTR | > 35% | 29.4% | Below target |
| Zero-click rate | < 30% | 38.7% | Below target |
| CTR — head queries | > 50% | 48.3% | Below target |
| CTR — tail queries | > 25% | 18.9% | Below target |

CTR is below target across every measured dimension. This report establishes the pre-hybrid-search baseline for comparison after the planned Q2 hybrid rollout. The data confirms the case made in the Q1 feasibility review: relevance quality for tail queries is the primary driver of low CTR.

## Key Highlights

- **Tail query CTR is the biggest gap**: Queries in the bottom 40% by frequency have a CTR of 18.9% vs. the 25% target. These queries often return loosely relevant or zero results, causing users to abandon rather than click.
- **Zero-click rate at 38.7%**: Nearly 4 in 10 searches result in no click at all. Of these, 34% are zero-result queries (no results returned) and 66% are dissatisfied with result quality (results shown but not clicked).
- **Position bias is steep**: CTR drops from 49.8% at position 1 to 12.3% at position 5. This suggests users are not trusting the ranking enough to scroll past the first two results.

## Active Initiatives

1. **Hybrid search rollout** (Q2): Expected to reduce zero-result rate and improve tail query recall, directly addressing the largest CTR gap.
2. **Result snippet quality improvement**: Improving highlight generation to show more relevant excerpt context around matched terms.
3. **Ranking diversity**: Investigating position-bias mitigation via diversified result sets for head queries.

## Incidents

No incidents this period.

## Risks

- **Critical**: CTR gap is directly tied to revenue — lower CTR means fewer product page views and conversions. Each 1% CTR improvement estimated at $180K ARR impact.
- **Critical**: Zero-click rate of 38.7% indicates users are not finding value in search. Risk of users bypassing search for direct navigation.
- **Critical**: Tail query CTR at 18.9% — semantic search rollout is the primary planned mitigation and must succeed.

## Next Month Focus

- Begin hybrid search rollout (25% of queries)
- Measure CTR delta in hybrid vs. control cohort weekly
- Prototype improved result snippet highlighting
- Investigate position-bias reduction strategies for head queries
