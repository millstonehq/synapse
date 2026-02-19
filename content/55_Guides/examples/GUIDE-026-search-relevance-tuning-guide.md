---
id: GUIDE-026
type: guide
title: Search Relevance Tuning Guide
status: draft
owner: Engineering Team
created: '2024-08-26T05:18:11.243Z'
updated: '2025-07-09T12:05:17.784Z'
tags:
  - guide
  - search-platform
summary: Search Relevance Tuning Guide
audience: partner
related_systems:
  - SYSTEM-024
  - SYSTEM-023
related_sops:
  - SOP-048
  - SOP-046
example: true
---

## Why Relevance Tuning Matters

A search index that returns technically correct results in the wrong order frustrates users just as much as one that returns no results at all. Relevance tuning is the process of adjusting how the ranking algorithm weights and combines signals to surface the most useful result at rank 1. Done well, it increases click-through rate, reduces query reformulation, and builds user trust in the search experience.

## Understanding the Scoring Model

The Search Platform uses BM25 as the base similarity algorithm. BM25 scores documents by how well the query terms match the document's content, taking into account term frequency, inverse document frequency (rare terms score higher), and field length normalization. On top of BM25, function score modifiers can boost documents based on recency, popularity, or user-personalization signals.

When diagnosing a relevance problem, start with the Explain API to see the score breakdown for a specific query and document pair. This shows exactly which fields contributed to the score and by how much, allowing you to pinpoint whether the issue is field weight, analyzer mismatch, or a function score override.

## Adjusting Field Weights

The most impactful tuning lever is field boosting. If the `title` field consistently outperforms `body` for relevance, increase the title boost:

```json
{
  "query": {
    "multi_match": {
      "query": "network configuration",
      "fields": ["title^3", "summary^2", "body^1"],
      "type": "best_fields"
    }
  }
}
```

Test weight changes against a set of known-good and known-bad query/result pairs before deploying. A weight change that improves 10 queries but degrades 5 others may not be a net win.

## Tuning Analyzers for Better Matching

Poor relevance is often caused by tokenization mismatches — the query and the document do not share enough terms after analysis. Use the Analyze API to debug:

```
POST /<index>/_analyze
{"analyzer": "standard", "text": "network configurations"}
```

If the query "configurations" does not match documents containing "configuring" or "configure", adding a stemming analyzer (e.g., English stemmer) will improve recall. However, stemming can also introduce false positives, so test carefully.

## Synonym Expansion

Synonyms allow queries using one term to match documents using an equivalent term. They are most effective for domain-specific vocabulary where users and content authors use different terminology (e.g., "VM" vs "virtual machine", "k8s" vs "kubernetes"). Synonyms are managed in the synonyms dictionary and applied at query time via the search analyzer.

## Measuring the Impact of Changes

Never deploy a relevance change without measuring it. Use the offline NDCG@10 benchmark against the annotated query set to quantify the change. If the change improves NDCG@10 by more than 1 percentage point with no regression in the top 20 degraded queries, it is worth promoting to an A/B test for live validation.
