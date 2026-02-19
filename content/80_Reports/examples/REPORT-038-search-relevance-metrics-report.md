---
id: REPORT-038
type: report
title: Search Relevance Metrics Report
status: draft
owner: Search Tech Lead
created: '2025-07-27T03:55:36.886Z'
updated: '2026-07-08T20:17:11.760Z'
tags:
  - report
  - search-platform
summary: Search Relevance Metrics Report
company: SearchPlatform
report_month: 2025-01
report_type: company
overall_health: good
confidence: medium
active_initiatives_count: 5
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| NDCG@10 (online) | > 0.80 | 0.84 | On target |
| Click-through rate (CTR) | > 38% | 40.2% | On target |
| Zero-result rate | < 3% | 2.8% | On target |
| Mean Reciprocal Rank (MRR) | > 0.60 | 0.63 | On target |
| Relevance model accuracy | > 82% | 85% | On target |
| Position-1 CTR | > 55% | 57.4% | On target |

January marks the first month all five core relevance metrics have been simultaneously on target since the platform launched. The LightGBM model promotion in March 2025 and the hybrid search rollout in Q2 2025 together drove the improvements. The team is now focused on closing the remaining gap between online and offline NDCG metrics.

## Key Highlights

- **Hybrid search fully rolled out**: 100% of queries are now scored using Reciprocal Rank Fusion of BM25 and ANN results. CTR on tail queries (bottom 20% by frequency) improved 4.8% month-over-month.
- **Zero-result rate below 3%**: For the first time, the zero-result rate is within target. Semantic fallback handles most formerly zero-result keyword queries by finding semantically similar documents.
- **Relevance model retrain scheduled**: The current model was trained on data through September 2025. A retrain with fresher click data is scheduled for Q1 end to capture recent content shifts.

## Active Initiatives

1. **Relevance model retrain**: Training pipeline runs; model expected to improve NDCG@10 by further 0.02-0.03 based on offline evaluation.
2. **Query understanding improvements**: Intent classification (navigational vs. informational) being integrated into the query rewrite layer to apply different ranking strategies per intent.
3. **Personalized ranking**: A/B test of user-affinity signals is live for 10% of logged-in users. Early CTR uplift of 1.2%.

## Incidents

No incidents affecting relevance metrics this period.

## Risks

No critical risks at this time.

- **Medium**: Online/offline NDCG gap is 0.03 (online 0.84, offline 0.87). Gap indicates the evaluation set may not represent recent query distribution. Refresh the evaluation set with recent queries.
- **Low**: Personalization A/B test showing 1.2% CTR uplift but small sample size; statistical significance not yet reached.

## Next Month Focus

- Complete relevance model retrain and promote to production
- Refresh evaluation query set with recent click data
- Expand personalization A/B test to 25% of logged-in users
- Begin intent classification integration into query rewrite layer
