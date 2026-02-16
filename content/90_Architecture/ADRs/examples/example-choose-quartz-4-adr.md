---
id: ADR-0001
type: adr
title: Choose Quartz 4 for Documentation Publishing
status: accepted
owner: Technology Operating Partner
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - adr
  - documentation
  - tooling
summary: >-
  Records the decision to adopt Quartz 4 as our documentation publishing
  platform. USE AN ADR when a significant architectural or technical
  DECISION has been made and you need to record the context, the
  decision itself, and its consequences for future reference. ADRs
  answer "why did we choose X over Y?" They are immutable records -
  if a decision is reversed, you write a new ADR that supersedes the
  old one rather than editing it. Compare: a TDD designs the full
  technical implementation; an ADR captures a single decision point.
  A System doc describes the running result; an ADR explains why it
  was built that way.
example: true
---

## Context

We need a publishing platform for our Obsidian-based documentation vault that supports:

- **Obsidian compatibility**: Wikilinks, backlinks, tags, and the knowledge graph must work natively without manual conversion
- **Internal hosting**: The platform must be self-hostable - no reliance on third-party SaaS for viewing internal documentation
- **Minimal glue code**: We want to point at a content directory and have it work, not maintain a complex build pipeline with custom plugins
- **Search**: Full-text search across all documents without external search services

The documentation vault currently contains ~200 documents across 17 content types (policies, standards, processes, SOPs, TDDs, ADRs, etc.) and is expected to grow to 500+ within a year.

## Decision

Adopt **Quartz 4** as our documentation publishing platform.

Configuration: Set `contentDir` to `./content`, enable backlinks, tags, and graph plugins by default. Use the default theme with minor SCSS customizations for branding. Deploy as a static site behind nginx.

The Quartz submodule will live at `packages/site/quartz` with our configuration overlay at `packages/site/quartz.config.ts`.

## Consequences

**Positive:**
- Obsidian wikilink syntax works out of the box - no conversion step needed
- Backlinks and graph view provide native knowledge navigation
- Static site output means simple deployment (nginx, S3, any CDN)
- Active open-source community with regular updates
- Built-in full-text search via client-side index

**Negative:**
- Theming is less flexible than Docusaurus - we're constrained to Quartz's layout system and SCSS variables
- No built-in CMS editing experience (addressed separately with Decap CMS integration)
- TypeScript-based build requires Node.js in the CI pipeline
- Less ecosystem support than Docusaurus for custom plugins (smaller community)

**Neutral:**
- Performance is comparable to other static site generators for our document count
- Migration cost is low since our content is already in standard Markdown with YAML frontmatter

## Alternatives Considered

**Docusaurus with custom plugins:**
- Pro: Largest ecosystem, most flexible theming, React-based
- Con: No native Obsidian wikilink support - would require a custom remark plugin to convert wikilinks to standard Markdown links. Backlinks and graph would need custom plugins. Significant glue code.
- Rejected because: The glue code to support Obsidian semantics would be a maintenance burden that defeats the "minimal glue" requirement.

**MkDocs with mkdocs-roamlinks plugin:**
- Pro: Python-based (simpler CI), good search, mature ecosystem
- Con: The roamlinks plugin supports basic wikilinks but not the full Obsidian syntax (aliases, block references). No graph view. Limited backlink support.
- Rejected because: Incomplete Obsidian compatibility would force us to use a subset of Obsidian features, limiting the vault's usefulness.

**Obsidian Publish:**
- Pro: Perfect Obsidian compatibility (it IS Obsidian), zero configuration
- Con: SaaS-only, cannot self-host. $8/month per site. Content is hosted on Obsidian's servers.
- Rejected because: Violates the internal hosting requirement. Sensitive documentation cannot be hosted on third-party infrastructure.
