---
id: ADR-0021
type: adr
title: Adopt OpenSearch for New Clusters
status: approved
owner: Principal Engineer
created: '2025-05-28T00:01:51.690Z'
updated: '2026-02-10T23:16:19.234Z'
tags:
  - adr
  - search-platform
summary: Adopt OpenSearch for New Clusters
example: true
---

## Context

Elastic changed the Elasticsearch license from Apache 2.0 to the Server Side Public License (SSPL) beginning with version 7.11 (January 2021). SSPL is not considered open-source by the OSI, and it places restrictions on offering Elasticsearch as a managed service. While self-hosted use for internal purposes is not directly restricted by SSPL, the licensing change introduces legal uncertainty about long-term terms and the pricing trajectory of Elastic's commercial features.

AWS forked Elasticsearch 7.10 (the last Apache 2.0 release) and created OpenSearch, now maintained under the Apache 2.0 license. OpenSearch has reached version 2.x with feature parity on the capabilities we use (full-text search, aggregations, HNSW vector search, k-NN plugin, index aliases, and ISM policies).

The existing production Elasticsearch cluster is on 8.x and we do not plan to migrate it. The question is: should new clusters provisioned from this point forward use Elasticsearch or OpenSearch?

## Decision

All **new Elasticsearch-compatible clusters** provisioned from this point forward will use **OpenSearch 2.x** rather than Elasticsearch.

This applies to: new analytics clusters, new development/staging clusters, and any additional production clusters created for new data sets (e.g., a dedicated vector search cluster for the AI search initiative).

The existing production cluster running Elasticsearch 8.x will **not** be migrated in the near term. Migration of the existing cluster will be evaluated separately when the cluster next requires a major version upgrade.

## Consequences

**Positive:**
- OpenSearch is Apache 2.0 licensed — no SSPL legal risk for current or future use cases
- AWS OpenSearch Service provides managed hosting with first-class AWS integration (IAM auth, VPC, KMS encryption)
- API compatibility with Elasticsearch 7.10 is high; our existing client libraries and index templates require minimal changes
- OpenSearch 2.x includes the k-NN plugin for vector search, matching the capability we use in Elasticsearch 8.x

**Negative:**
- OpenSearch diverges from Elasticsearch over time; new Elasticsearch features (e.g., ES|QL, Elastic AI Assistant) will not be available in OpenSearch
- Our team now needs to maintain operational knowledge of two compatible-but-divergent engines (ES 8.x for the existing cluster, OpenSearch 2.x for new clusters)
- Some Elasticsearch 8.x Query DSL features (e.g., `semantic_text` field type, ELSER model integration) are Elastic-proprietary and unavailable in OpenSearch

**Neutral:**
- Client libraries (elasticsearch-py, elasticsearch-js) can target OpenSearch by pointing to the OpenSearch endpoint and using compatible API calls; dedicated OpenSearch clients also available
- Migration path from the existing ES 8.x cluster to OpenSearch is feasible via reindex, but not committed in this ADR

## Alternatives Considered

**Continue using Elasticsearch 8.x for all new clusters:**
- Pro: Single engine to operate; access to latest Elastic features; existing team expertise applies
- Con: SSPL licensing risk; commercial licensing required if we use Elastic Cloud or proprietary features; pricing uncertainty as Elastic shifts features behind paid tiers
- Rejected because: SSPL legal risk is unacceptable for new workloads; OpenSearch provides equivalent functionality under a clear open-source license

**Self-host Elasticsearch 7.10 (last Apache 2.0 version):**
- Pro: Apache 2.0 licensed; proven stability; Elastic provides security patches under SSPL (not Apache 2.0)
- Con: No longer receiving security patches from Elastic; stuck on a 5-year-old version without a forward path; no vector search support
- Rejected because: Security patch obligation is critical; a frozen-at-7.10 cluster is a security liability
