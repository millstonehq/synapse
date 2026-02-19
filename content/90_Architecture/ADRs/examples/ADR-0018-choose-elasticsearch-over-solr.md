---
id: ADR-0018
type: adr
title: Choose Elasticsearch Over Solr
status: approved
owner: Principal Engineer
created: '2024-11-06T10:46:03.902Z'
updated: '2026-04-16T05:53:33.126Z'
tags:
  - adr
  - search-platform
summary: Choose Elasticsearch Over Solr
example: true
---

## Context

The Search Platform requires a distributed full-text search engine capable of supporting the product's current needs and anticipated growth. At the time of this decision, the platform indexed approximately 5 million documents and served 3 million queries per day. The projected 3-year growth target is 50 million documents and 20 million queries per day.

Two viable open-source candidates were evaluated over a 6-week proof of concept: Apache Solr 9.x and Elasticsearch 8.x. Both are built on Apache Lucene and offer comparable raw indexing and query performance at our current scale. The evaluation focused on operational characteristics, ecosystem maturity, and alignment with our team's existing skills.

The team had prior production experience with Elasticsearch at a previous employer but no Solr production experience. Operational risk weighed heavily in the decision given the team's size (4 engineers) and the criticality of search to revenue.

## Decision

We will adopt **Elasticsearch 8.x** as the primary search engine for the Search Platform.

We will deploy a 3-node cluster (all nodes data + master-eligible) with 2 coordinating-only nodes for query fan-out. The cluster will use index aliases to separate read and write paths, enabling zero-downtime reindexing. Authentication and TLS will be enabled from day one using the built-in X-Pack security features.

## Consequences

**Positive:**
- Team has direct prior experience with Elasticsearch, reducing the ramp-up time and operational risk
- Elasticsearch REST API and Query DSL are well-documented with extensive community examples
- Kibana is included and provides immediate observability into cluster health and query analytics
- Dense vector and k-NN search (HNSW) are natively supported in 8.x, enabling future hybrid search without an engine migration
- Elastic Cloud option exists if we need to reduce operational burden in the future

**Negative:**
- Elasticsearch license changed to SSPL in 7.11+; future use of hosted Elastic Cloud involves commercial licensing if we need proprietary features
- JVM tuning and heap management add operational complexity compared to Solr's similar (but differently configured) JVM stack
- Elasticsearch does not have Solr's SolrCloud ZooKeeper-based coordination; the built-in cluster management is simpler but less familiar to engineers with deep Solr experience

**Neutral:**
- Both engines are backed by Apache Lucene, so underlying query semantics are equivalent
- Migration to OpenSearch (the AWS-maintained Elasticsearch fork) is low-effort if licensing or commercial terms change

## Alternatives Considered

**Apache Solr 9.x:**
- Pro: Mature project with long track record in enterprise search; strong faceting and schema management tooling
- Con: No native dense vector search support in Solr 9 (added only in Solr 9.x with limited HNSW support); team has no Solr production experience; SolrCloud requires ZooKeeper, adding another stateful dependency to manage
- Rejected because: Native vector search support is a near-term requirement (hybrid search is on the roadmap); team expertise with Elasticsearch reduces operational risk more than any Solr-specific advantage

**Typesense:**
- Pro: Very simple to operate; single binary; no JVM; excellent developer experience
- Con: Not designed for 50M+ document corpora; limited aggregation and faceting capabilities; sparse community for large-scale production deployments
- Rejected because: Does not meet the 50M document scale requirement; limited faceting support would require significant workarounds
