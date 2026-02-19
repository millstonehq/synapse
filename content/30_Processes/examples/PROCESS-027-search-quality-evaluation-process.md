---
id: PROCESS-027
type: process
title: Search Quality Evaluation Process
status: approved
owner: Platform Lead
created: '2024-12-18T03:41:39.738Z'
updated: '2025-12-21T18:48:17.517Z'
tags:
  - process
  - search-platform
summary: Search Quality Evaluation Process
related_standards:
  - STANDARD-029
  - STANDARD-026
related_sops:
  - SOP-044
  - SOP-047
related_systems:
  - SYSTEM-023
example: true
---

## Purpose

The Search Quality Evaluation Process establishes a repeatable method for measuring and tracking the quality of search results over time. It ensures that the team has objective data to detect relevance regressions, evaluate algorithm changes, and prioritize quality improvement work.

Without a structured evaluation process, ranking changes can subtly degrade search quality in ways that are not visible in operational metrics like latency and error rate but are clearly felt by users through poor result relevance.

## Scope

- Quarterly offline evaluation of search quality against annotated query-document relevance judgments
- Pre-deployment quality gates for algorithm and index changes
- User satisfaction signal collection via click-through rate, zero-result rate, and query reformulation rate

## Roles and Responsibilities

- **Search Engineer**: Maintains the annotated query set and runs NDCG benchmark evaluations
- **Data Scientist**: Performs statistical analysis on evaluation results and identifies significant regressions
- **Product Manager**: Reviews quality trends and prioritizes user-facing improvements
- **QA Engineer**: Maintains the regression test suite of known-good and known-bad query/result pairs

## Triggers

- Quarterly quality review cadence (scheduled)
- Pre-deployment gate for any change to ranking configuration or index schema
- User feedback spike indicating a sudden quality degradation

## Inputs

- Annotated query-document relevance judgment set (minimum 500 queries per major content domain)
- Current production index snapshot for offline evaluation
- Analytics data: CTR by query type, zero-result rate, session abandonment rate from past 30 days

## Outputs

- Quality evaluation report with NDCG@10, MRR, and zero-result rate metrics versus prior period baseline
- Regression query list identifying queries where rank position of the top-judged document worsened
- Quality trend dashboard updated with current evaluation results

## Steps

1. Export a representative sample of recent production queries (stratified by intent type) to use as the evaluation query set
2. Run the annotated query set against the current production index using the evaluation framework and compute NDCG@10, NDCG@20, and MRR
3. Compare results against the previous quarter's baseline; flag any metric that has declined by more than 2 percentage points
4. For flagged regressions, drill into the specific queries causing the decline and identify whether the cause is a ranking, indexing, or content problem
5. Collect user satisfaction signals from the analytics pipeline: CTR trend, zero-result rate, and query reformulation rate for the evaluation period
6. Compile findings into the Quality Evaluation Report; assign severity ratings to identified issues
7. Present findings to Product Manager in the monthly search quality review meeting and agree on a prioritized improvement backlog

## Controls

- Evaluation query sets must be reviewed and refreshed at least annually to remain representative
- NDCG@10 decline of more than 5 percentage points triggers a mandatory blocking investigation before any further ranking changes are deployed
- Evaluation results must be stored in the quality metrics repository for at least 2 years for trend analysis
