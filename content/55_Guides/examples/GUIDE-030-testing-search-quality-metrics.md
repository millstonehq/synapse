---
id: GUIDE-030
type: guide
title: Testing Search Quality Metrics
status: approved
owner: Engineering Team
created: '2024-03-16T17:54:56.433Z'
updated: '2025-10-21T22:00:47.807Z'
tags:
  - guide
  - search-platform
summary: Testing Search Quality Metrics
audience: internal
related_systems:
  - SYSTEM-024
  - SYSTEM-025
related_sops:
  - SOP-047
  - SOP-044
example: true
---

## Why Measure Search Quality

Operational metrics like latency and error rate tell you whether the search service is running, but not whether it is returning useful results. Search quality metrics close this gap by quantifying how well the ranked results match user intent. Without quality measurement, ranking changes can silently degrade user experience, and improvements have no objective baseline to compare against.

## Key Metrics Explained

**NDCG@K (Normalized Discounted Cumulative Gain)**: Measures ranking quality by weighting highly relevant results that appear early in the list more than those appearing later. NDCG@10 (at rank 10) is the primary offline benchmark metric. A score of 1.0 means perfect ranking; 0.0 means the worst possible ranking. Typical production search systems operate in the 0.6–0.8 range.

**MRR (Mean Reciprocal Rank)**: Measures how quickly the first relevant result appears. If the first relevant result is at rank 1, the reciprocal rank is 1.0; at rank 3, it is 0.33. MRR is a useful complement to NDCG for queries where users only care about the single best result.

**Zero-result rate**: The fraction of queries that returned no results. High zero-result rates indicate gaps in index coverage, overly strict query parsing, or missing synonyms. A zero-result rate above 5% usually warrants investigation.

## Building an Evaluation Dataset

An offline evaluation requires a set of query-document relevance judgments: for each test query, a human judge rates the relevance of the top results on a scale (e.g., 0 = not relevant, 1 = partially relevant, 2 = highly relevant). Judgments should be collected by domain experts or qualified users, not by engineers who built the ranking model.

Aim for at least 500 query-judgment pairs across the major query intent types in your domain. Update the judgment set quarterly to account for content changes that may make old judgments stale.

## Running the Evaluation

The evaluation framework takes the judgment set, issues each query against the current index, retrieves the ranked results, and computes NDCG and MRR scores against the judgments. Run the evaluation after any ranking or index change to detect regressions before they reach production:

```bash
python evaluate.py \
  --judgments judgments/q4-2024.jsonl \
  --index-url https://search-staging.example.com \
  --output-dir reports/
```

The output report lists per-query NDCG scores alongside the top 10 results for each query, making it easy to manually review the worst-performing queries and understand what is going wrong.

## Interpreting Results

A change that improves NDCG@10 by 1 percentage point or more (e.g., from 0.71 to 0.72) is meaningful and worth promoting to an A/B test. A change that improves the average but increases the number of queries with NDCG below 0.5 (the regression set) needs careful review — improving the average while creating more "terrible" queries is generally not a good trade-off.

Track evaluation results over time in the quality metrics dashboard to identify gradual quality drift between explicit experiments, which can indicate data quality issues in the upstream content pipeline.
