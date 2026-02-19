---
id: MEETING-046
type: meeting
title: AI-Powered Search Exploration Session
status: approved
owner: Principal Engineer
created: '2024-04-18T08:02:15.981Z'
updated: '2025-10-14T01:02:35.738Z'
tags:
  - meeting
  - search-platform
summary: AI-Powered Search Exploration Session
company: SearchPlatform
topic: AI-Powered Search Exploration Session
meeting_date: '2024-11-10T02:28:35.544Z'
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

- **Project**: Search Platform - AI Features Exploration
- **Topic**: AI-Powered Search Exploration Session
- **Date/Time**: 2024-11-10 10:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Scientist, ML Engineer
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Exploratory session to evaluate AI/ML capabilities for improving search: semantic search (dense vector / kNN), LLM-based query understanding, and AI-generated result summaries.

## Observations by Domain

- **Semantic / Vector Search**: Elasticsearch 8's kNN search supports dense vector fields; OpenAI and open-source embedding models (e.g., sentence-transformers) can generate document embeddings at indexing time; hybrid BM25 + kNN scoring is the recommended approach for production quality
- **Query Understanding**: LLM-based query expansion (using GPT-4 to expand sparse short queries into richer queries) showed 8% NDCG improvement in a prototype test; latency overhead was 120ms P50 — borderline acceptable
- **AI-Generated Summaries**: Generating abstractive summaries of top search results using an LLM can reduce pogo-sticking; user research from similar products shows 15-25% reduction in abandonment; cost per query is a concern at scale
- **Personalization**: Click history-based personalization using matrix factorization can improve CTR by 10-15% for returning users; requires user identity signal that is not currently available in anonymous search sessions
- **Infrastructure Readiness**: ES8 upgrade (planned for Q1 2025) is a prerequisite for kNN; GPU-accelerated embedding inference would require new infrastructure investment

## Key Metrics & Data Points

- **Prototype kNN semantic search NDCG@10**: 0.71 (vs. current BM25 NDCG@10 of 0.68)
- **Hybrid BM25 + kNN NDCG@10 in prototype**: 0.74 (better than either alone)
- **LLM query expansion latency overhead**: 120ms P50 added to query latency
- **Estimated cost of AI summaries at current query volume**: ~$8,000/month at GPT-4 pricing
- **Embedding model considered**: `sentence-transformers/all-MiniLM-L6-v2` (80ms inference, 384-dim vectors)

## Preliminary Scorecard Hooks

- Semantic Search Readiness: 3/5 - Technically feasible after ES8 upgrade; embedding infrastructure needs scoping
- LLM Query Understanding: 3/5 - Shows promise but latency overhead is at the boundary of acceptable SLO
- AI Summaries: 2/5 - High user impact but cost model needs work before commitment
- Infrastructure Readiness: 2/5 - ES8 upgrade and embedding service are prerequisites; 2-quarter lead time

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Embedding model inference adds unacceptable latency | High | Medium | ML Engineer | Evaluate ONNX-quantized embedding model for 3-5x latency reduction | 2025-01-15 |
| AI summary costs exceed budget at full traffic | Medium | High | Engineering Manager | Implement tiered strategy: AI summaries only for zero-click queries initially | 2025-02-01 |

## Decisions & Next Steps

### Decisions

- Prioritize hybrid BM25 + kNN search as the primary AI investment after ES8 upgrade
- Defer AI-generated summaries to H2 2025 pending cost modeling and ES8 stability
- Time-box the kNN feasibility spike to Sprint 24

### Action Items

- Evaluate quantized embedding model latency and accuracy (ML Engineer - 2024-12-01)
- Draft infrastructure requirements for embedding service (Principal Engineer - 2024-12-15)
- Cost model for AI summaries at 3 query volume scenarios (Engineering Manager - 2025-01-15)

### Follow-ups

- AI search roadmap review to be added to Q1 2025 planning session
- Share embedding model evaluation results with the wider engineering team
