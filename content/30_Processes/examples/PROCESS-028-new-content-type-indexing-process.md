---
id: PROCESS-028
type: process
title: New Content Type Indexing Process
status: draft
owner: Director of Engineering
created: '2025-08-17T03:32:59.184Z'
updated: '2025-07-18T06:41:56.370Z'
tags:
  - process
  - search-platform
summary: New Content Type Indexing Process
related_standards:
  - STANDARD-030
  - STANDARD-029
related_sops:
  - SOP-048
  - SOP-045
related_systems:
  - SYSTEM-023
example: true
---

## Purpose

The New Content Type Indexing Process defines how the Search Platform onboards a new class of documents (e.g., video transcripts, product listings, help articles) into the search index. Adding a new content type requires careful schema design, relevance signal definition, and integration testing to avoid degrading the quality of existing content types.

This process ensures that new content types meet the data governance requirements of [[STANDARD-030|Search Analytics Event Standard]] before going live, and that the ingestion pipeline is verified end-to-end before production traffic is enabled.

## Scope

- Onboarding of any new document type that will be served in search results
- Changes that materially expand the field coverage of an existing content type
- Integration of a new source system with the search ingestion pipeline

## Roles and Responsibilities

- **Search Platform Engineer**: Designs the index mapping, builds the ingestion adapter, and leads testing
- **Content/Data Owner**: Provides a representative sample dataset and documents field semantics and ownership
- **Platform Lead**: Approves the mapping design and grants permission to create the production index
- **SRE On-Call**: Monitors cluster health during initial bulk load of the new content type

## Triggers

- Product team requests to surface a new content type in search results
- A new data source is onboarded that contains content not currently indexed
- A content migration requires re-modeling an existing type with an expanded schema

## Inputs

- Content type specification: list of fields, field types, cardinalities, and sample documents
- Data volume estimate: expected document count, daily ingestion rate, and field size distributions
- Relevance requirements: which fields are most important for text matching and ranking

## Outputs

- Production index with validated mapping and populated documents
- Ingestion pipeline configured and monitored in the Search Platform's pipeline dashboard
- Analytics events registered per [[STANDARD-030|Search Analytics Event Standard]] to track CTR and quality for the new content type

## Steps

1. Work with the Content/Data Owner to document all fields, their types, expected cardinalities, and which contain PII subject to [[STANDARD-029|Search Autocomplete API Standard]] restrictions
2. Design the Elasticsearch mapping and create a draft mapping file in version control for Platform Lead review
3. Create a staging index with the approved mapping and bulk-load a representative sample dataset (minimum 10,000 documents)
4. Run relevance evaluation queries against the staging index and document baseline NDCG@10 for the new content type
5. Build or configure the production ingestion adapter; run end-to-end integration tests using the sample dataset
6. Load test the ingestion pipeline at 150% of expected peak throughput; verify cluster resource headroom remains above 30%
7. Obtain Platform Lead approval and deploy the new index and ingestion pipeline to production; start with read-only shadow mode before enabling result serving
8. Enable results for the new content type in production search; monitor CTR and zero-result rate for 7 days before declaring the onboarding complete

## Controls

- New content type mappings must be reviewed and approved by Platform Lead before production index creation
- PII field exclusions must be confirmed with the data privacy officer before bulk load
- Load testing is mandatory; new content types must not be enabled in production without a completed load test
