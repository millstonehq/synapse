---
id: MEETING-050
type: meeting
title: Semantic Search Feasibility Review
status: approved
owner: Product Manager
created: '2025-12-28T12:03:15.212Z'
updated: '2025-09-15T14:48:08.941Z'
tags:
  - meeting
  - search-platform
summary: Semantic Search Feasibility Review
company: SearchPlatform
topic: Semantic Search Feasibility Review
meeting_date: '2025-07-06T00:08:00.900Z'
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

- **Project**: Search Platform
- **Topic**: Semantic Search Feasibility Review
- **Date/Time**: 2025-07-06 10:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Evaluating the technical and product feasibility of adding semantic/vector search to the existing keyword-based search platform. Stakeholders from both product and engineering aligned on scoping and risk.

## Observations by Domain

- **Indexing Infrastructure**: Current Elasticsearch cluster supports dense_vector fields in 8.x; no major infrastructure changes needed for initial vector indexing, but storage overhead is ~3x per document.
- **Query Latency**: Approximate nearest-neighbor (ANN) search via HNSW adds ~15-30ms overhead at current corpus size. Acceptable for P95 targets if combined with pre-filtering.
- **Embedding Pipeline**: No internal embedding service exists today. Options are a hosted provider (OpenAI embeddings) or self-hosted model (sentence-transformers). Hosted adds ~80ms per query round-trip.
- **Relevance Quality**: Manual evaluation on 200 sampled queries shows semantic recall improves zero-result rate from 4.2% to 1.1%, though precision on head queries is slightly worse without reranking.
- **Operational Complexity**: Two index formats to maintain (keyword + vector) increases operational surface. Hybrid scoring must be tuned per content type.

## Key Metrics & Data Points

- **Current zero-result rate**: 4.2% of daily queries
- **Semantic zero-result rate (test)**: 1.1% on sampled evaluation set
- **ANN query overhead**: 15-30ms P95 at current corpus size (~8M documents)
- **Embedding storage overhead**: ~3x vs. keyword-only index
- **Corpus growth rate**: ~200K new documents/month, requiring continuous embedding backfill

## Preliminary Scorecard Hooks

- Indexing Infrastructure: 4/5 - ES 8.x supports vector fields natively; storage costs manageable
- Query Latency Impact: 3/5 - ANN overhead acceptable today but needs monitoring at scale
- Embedding Pipeline Readiness: 2/5 - No internal service; dependency on external provider is a risk
- Relevance Quality: 4/5 - Strong improvement on zero-result and tail queries
- Operational Complexity: 2/5 - Dual-index maintenance is a meaningful ongoing burden

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| External embedding provider latency degrades P95 query SLA | High | Medium | Tech Lead | Implement async pre-embedding at ingest time; cache vectors in index | 2025-08-15 |
| Vector index storage costs exceed budget at scale | Medium | Medium | Principal Engineer | Benchmark storage at 20M docs before committing; evaluate quantization | 2025-08-01 |
| Hybrid scoring difficult to tune across content types | Medium | High | Tech Lead | Build offline evaluation harness with NDCG metrics before GA | 2025-09-01 |
| Backfill of existing corpus delays launch | Low | High | Engineering Manager | Parallel backfill job; launch with partial corpus covered | 2025-09-15 |

## Decisions & Next Steps

### Decisions

- Proceed with a 60-day proof-of-concept using a shadow index approach — semantic results served in parallel, not replacing keyword results
- Use OpenAI text-embedding-3-small as the embedding provider for the PoC; evaluate cost and latency before committing
- Hybrid scoring will use Reciprocal Rank Fusion (RRF) as the default merge strategy

### Action Items

- Build embedding backfill pipeline for top 1M documents (Tech Lead - 2025-07-25)
- Configure shadow vector index on non-production cluster (Principal Engineer - 2025-07-20)
- Define evaluation set and NDCG baseline for relevance comparison (Product Manager - 2025-07-18)

### Follow-ups

- Reconvene in 30 days to review PoC latency and relevance metrics
- Escalate to VP Engineering if storage cost projection exceeds $5K/month
