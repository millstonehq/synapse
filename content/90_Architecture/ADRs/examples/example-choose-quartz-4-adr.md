---
id: ADR-0001
type: adr
title: Choose Quartz 4 for Publishing
status: proposed
owner: Technology Operating Partner
created: "2025-10-18T19:48:03.132Z"
updated: "2025-10-18T19:48:03.133Z"
tags:
  - adr
example: true
---
# Choose Quartz 4 for Publishing

## Context
We need Obsidian-compatible publishing with backlinks and graph, minimal glue, and internal hosting.

## Decision
Adopt Quartz 4 with contentDir ./content; enable backlinks, tags, and graph by default.

## Consequences
Simple setup; Obsidian semantics preserved; theming is less flexible than Docusaurus.

## Alternatives Considered
- Docusaurus with custom plugins
- MkDocs + mkdocs-roamlinks

## References
- https://quartz.jzhao.xyz/
