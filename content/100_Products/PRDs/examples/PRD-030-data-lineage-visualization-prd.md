---
id: PRD-030
type: prd
title: Data Lineage Visualization PRD
status: approved
owner: Head of Product
created: '2025-08-01T21:39:17.832Z'
updated: '2025-04-25T17:54:53.383Z'
tags:
  - prd
  - data-pipeline
summary: Data Lineage Visualization PRD
related_tdds:
  - TDD-028
  - TDD-026
example: true
related_standards:
  - STANDARD-032
---

## Summary

Build a Data Lineage Visualization product that provides an interactive graph-based UI for exploring column-level lineage across the data lake. Engineers and analysts can trace a column from a consumer dashboard back to its originating Kafka topic, perform upstream impact analysis before making source changes, and identify all downstream consumers affected by a proposed upstream modification. The visualization layer sits on top of the Data Lineage Tracker API. Technical design is driven by [[TDD-028|TDD-028: Schema Evolution Handler]] and [[TDD-026|TDD-026: Real-Time Event Processing Engine]], and must comply with [[STANDARD-032|STANDARD-032]].

## Goals

- Enable any engineer to trace a data column from a mart table to its originating source within 5 minutes without Data Engineering assistance
- Reduce uncoordinated breaking schema changes by 80% by making consumer impact visible before a change is made
- Give Data Engineering a first-class impact analysis tool for evaluating proposed upstream changes
- Surface lineage data that currently exists in the Data Lineage Tracker API but is inaccessible to non-API users

## In Scope

- Interactive DAG visualization for table-level and column-level lineage traversal
- Upstream traversal: "What are all the sources for this table/column?"
- Downstream impact analysis: "What downstream tables/columns would be affected if I change this source?"
- Node detail panel: table metadata, quality score, freshness, schema summary
- Path highlighting: show the shortest path between any two nodes in the lineage graph
- Export: generate lineage report (PDF/CSV) for a selected subgraph

## Out of Scope

- Lineage data ingestion (sourced from Data Lineage Tracker API; no new parsing in this product)
- Historical lineage comparison (point-in-time traversal is a v2 feature)
- Automated impact assessment notifications (notify stakeholders when their downstream is affected — v2)

## Users and Flows

**Data Engineers**: Before modifying a source Iceberg table schema, traverse downstream impact to identify all affected consumers; use the impact list to notify affected teams before deployment.

**Data Analysts**: Trace a suspect column value upstream to its raw Kafka source; identify which ingestion and transformation steps could have introduced an anomaly.

**Engineering Leadership**: Review data flow architecture diagrams for a domain without needing to read code or query the Data Lineage Tracker API directly.

## Requirements

- Graph renders within 5 seconds for traversal depth up to 5 hops on the current production lineage graph (~200 nodes)
- User can select any table or column as the starting node for traversal
- Traversal depth configurable from 1 to 10 hops
- Node panel shows table metadata (layer, schema, quality score, last updated) without a separate page load
- Downstream impact analysis highlights all nodes reachable from the selected node
- Export generates a lineage report with node list, edge list, and metadata table for the visible subgraph

## KPIs

- **Impact analysis adoption**: Data Engineering uses the tool for 100% of schema change reviews within 60 days of launch (measured by tool access logs)
- **Breaking change reduction**: Uncoordinated breaking schema changes (measured by Schema Registry compatibility rejections caused by missing consumer notification) reduced by 80% within 90 days
- **Time-to-trace**: Engineer can trace a column from mart to Kafka source in < 5 minutes (measured by user research)
- **Graph render performance**: P95 render time < 5 seconds for depth-5 traversal

## Information Architecture

- All lineage data served from the Data Lineage Tracker REST API (no direct DynamoDB access)
- Node metadata augmented with quality scores from the quality_results API
- Table metadata (freshness, schema) from the Iceberg Glue Catalog API

## Data Model

Core entities:

- **LineageGraphView**: Client-side graph state. Fields: `root_node_id`, `direction`, `depth`, `nodes`, `edges`, `highlighted_path`
- **NodeDetail**: Panel data for a selected node. Fields: `node_id`, `table`, `layer`, `quality_score`, `last_updated`, `column_count`, `upstream_count`, `downstream_count`

## Non-Functional

- Graph rendering must not degrade below 5 seconds for depth-5 traversal under standard office network conditions
- Authentication via SSO; no anonymous access
- Lineage API calls use read-only credentials; no writes to the lineage graph from the UI
- Export reports must not include PII column names (PII columns displayed as `[REDACTED]` in visualization and export)

## Constraints

- Must use the Data Lineage Tracker REST API as the exclusive data source; no direct DynamoDB queries
- Frontend must be accessible from the data catalog without a separate login (shared SSO session)
- Graph visualization library must support at least 500 nodes without rendering degradation

## Risks

- **Graph rendering performance on large lineage graphs**: Complex multi-hop traversals with 500+ nodes could degrade browser performance. Mitigation: Virtual rendering for off-screen nodes; maximum graph size capped at 200 visible nodes with depth-limit enforcement.
- **Lineage accuracy perception**: If the lineage graph is incomplete (e.g., for tables without dbt models), users may trust incorrect impact analysis. Mitigation: Confidence indicator per node showing whether lineage is complete or partial.

## Milestones

### M1: Core Graph Visualization (Week 1-4)

#### Deliverables

- Interactive graph rendering for table-level lineage
- Upstream and downstream traversal from any selected node
- Node detail panel with metadata

#### Acceptance Criteria

- Depth-5 traversal renders in < 5 seconds for any Tier-1 table
- Node detail panel loads without additional page navigation
- All 200+ production tables navigable from the root view

### M2: Column-Level and Impact Analysis (Week 5-7)

#### Deliverables

- Column-level lineage toggle (show/hide column nodes on top of table graph)
- Downstream impact highlighting for a selected source node
- Path highlighting between any two selected nodes

#### Acceptance Criteria

- Column-level graph renders correctly for tables with known dbt column lineage
- Downstream impact highlight correctly identifies all reachable nodes
- Path between two nodes highlights in < 2 seconds

### M3: Export and Adoption (Week 8-9)

#### Deliverables

- Lineage report export (PDF/CSV) for visible subgraph
- Integration into Data Catalog table detail page (lineage tab)
- Onboarding documentation and Data Engineering team workflow update

#### Acceptance Criteria

- Export generates correct node and edge list for the visible subgraph
- Lineage tab accessible from Data Catalog table detail page without separate login
- Data Engineering SOP updated to require lineage visualization review before schema change deployments
