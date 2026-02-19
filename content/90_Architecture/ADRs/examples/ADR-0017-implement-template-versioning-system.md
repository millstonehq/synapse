---
id: ADR-0017
type: adr
title: Implement Template Versioning System
status: approved
owner: Tech Lead
created: '2024-09-27T17:58:48.068Z'
updated: '2026-02-03T03:59:53.594Z'
tags:
  - adr
  - notification-service
summary: Implement Template Versioning System
example: true
supersedes: ADR-0015
---

## Context

The Email Delivery Service currently renders notification emails using templates referenced by slug only (e.g., `order-confirmation`). When a template is updated, the change takes effect immediately for all in-flight and future notifications using that slug. This has caused three production incidents in Q4 2024 where template content changes (copy updates, new required variables) broke in-flight notifications that were expecting the previous template structure.

Notification producers currently have no way to pin their notifications to a specific template version, preview a template change before publishing, or roll back to a previous version if a change causes rendering errors. The template management process is entirely manual and undocumented.

We need a versioning system that allows template changes to be made safely without affecting producers that have not yet migrated to the new version, and that provides a clear audit trail of template changes.

## Decision

We will implement a **semantic version numbering system** for notification templates. Each template will have a major version (e.g., `order-confirmation@v2`) stored in the templates database. Producers will reference templates using the `slug@version` format. The routing engine will resolve the latest minor/patch version within the specified major version.

A template publishing workflow will be added: templates can exist in `draft`, `published`, or `deprecated` states. Only `published` templates can be used in production sends. The previous version is moved to `deprecated` status when a new version is published, but remains active for producers that reference it explicitly.

## Consequences

**Positive:**
- Producers can pin their notification sends to a specific major template version, preventing unexpected breakage when templates are updated
- Template changes can be staged in `draft` state and previewed before publishing
- Deprecated versions remain active for a configurable grace period, giving producers time to migrate
- Full audit trail of template changes (who published, when, what changed) stored in the `template_versions` table

**Negative:**
- Producers must update their notification send calls to include a version reference; this requires a migration of all existing integrations
- Template lifecycle management (publishing, deprecating, cleanup) adds operational overhead
- The `deprecated` grace period means multiple template versions may be active simultaneously, increasing storage and cache complexity

**Neutral:**
- The unversioned slug reference will continue to work by resolving to the latest published version; this provides backward compatibility for producers that do not immediately migrate
- The unversioned endpoint will be deprecated 6 months after the versioning system launches

## Alternatives Considered

**Immutable templates with new slug per change:**
- Pro: Simple — each template change creates a completely new slug; no version resolution logic needed
- Con: Slug proliferation becomes unmanageable; no semantic relationship between template versions; discovery of the current canonical template for a notification type becomes difficult
- Rejected because: The operational overhead of slug management outweighs the simplicity benefit

**Git-based template management with SHA references:**
- Pro: Full version history available; familiar workflow for engineers
- Con: Requires git integration in the template loading path; adds deployment dependencies; non-engineers (content writers, marketing) cannot manage templates without git knowledge
- Rejected because: The content authorship requirement means the versioning system must be usable without git
