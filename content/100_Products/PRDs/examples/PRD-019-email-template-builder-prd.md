---
id: PRD-019
type: prd
title: Email Template Builder PRD
status: proposed
owner: Product Manager
created: '2024-04-10T01:28:53.750Z'
updated: '2026-11-23T14:27:41.042Z'
tags:
  - prd
  - notification-service
summary: Email Template Builder PRD
related_tdds:
  - TDD-016
  - TDD-020
example: true
related_standards:
  - STANDARD-024
---

## Summary

Build a no-code email template builder that enables marketing and product teams to create, edit, preview, and publish notification email templates without requiring engineering involvement. Currently all email template changes require an engineer to edit Handlebars source files, submit a PR, and deploy. This creates a bottleneck for content teams and slows the iteration cycle for email campaigns.

## Goals

- Enable marketing and content teams to independently create and update email notification templates
- Reduce template change cycle time from 3-5 days (requiring eng) to same-day (self-service)
- Ensure all templates published through the builder meet accessibility and deliverability standards automatically

## In Scope

- Drag-and-drop block-based email template builder (text, image, button, divider, columns)
- Visual preview rendering (desktop and mobile viewport)
- Variable placeholder insertion with type hints (`{{firstName}}`, `{{orderTotal}}`)
- Template versioning integration — publishes as a new version under the existing versioning system
- Pre-publish validation: spam score check, mobile rendering test, required variable schema check
- Template library: save and clone templates as starting points
- Role-based access: Marketing can create/edit; Engineering can approve/publish

## Out of Scope

- Plain-text email editing (auto-generated from HTML)
- SMS template editing (separate tool, different constraints)
- Transactional email template editing (Marketing only has access to promotional and digest templates; transactional templates require engineering approval)
- A/B testing within the builder (separate initiative)

## Users and Flows

**Marketing content creators** use the builder to create new email templates or update existing ones. They drag blocks onto the canvas, edit copy, insert variable placeholders from the available variable picker, preview across viewports, and submit for review.

**Engineering approvers** review submitted templates, check the variable schema against the notification producer's requirements, and publish to the template versioning system. This gate exists for transactional templates only; marketing templates can be self-published by senior marketers.

**The routing engine** uses templates published through the builder identically to templates created manually — there is no distinction at the delivery layer. The builder is a creation interface over the same template store.

## Requirements

- Block types: text, image, button CTA, horizontal rule, 1-column and 2-column layouts, header, footer
- Variable picker shows all declared variables for the selected notification type with type hints
- Mobile preview renders an accurate simulation of Gmail iOS and Outlook mobile rendering
- Pre-publish spam score check: reject if spam score > 3/10
- Pre-publish mobile rendering test: validate rendering on 5 standard mobile clients
- Template versioning: each publish creates a new minor version; breaking variable schema changes require a new major version
- All published templates must include a visible unsubscribe link (enforced by validator)

## KPIs

- **Self-service adoption**: > 80% of marketing email template changes made via builder within 6 months
- **Cycle time**: Average template change cycle time reduced from 4 days to < 4 hours
- **Deliverability**: No deliverability regression (spam score average remains < 2/10) after builder launch

## Information Architecture

- This PRD in `100_Products/PRDs/`
- Routing Engine TDD [[TDD-016|TDD-016]] covers the template resolution pipeline the builder publishes into
- SMS Abstraction Layer TDD [[TDD-020|TDD-020]] is out of scope for this feature
- Template versioning system reference: see ADR-0017

## Data Model

- **TemplateBlock**: `id`, `type`, `content`, `styles{}`, `order`
- **BuilderTemplate**: `id`, `name`, `notificationType`, `blocks[]`, `variableSchema{}`, `status` (draft|review|published), `createdBy`, `publishedVersion`
- Published templates are stored in the existing `templates` table in the versioned format; the builder is the authoring layer only

## Non-Functional

- Builder UI must load within 2 seconds on a standard laptop
- Pre-publish validation (spam check + mobile rendering) must complete within 60 seconds
- Templates rendered from builder output must be identical to manually authored templates at the delivery layer

## Constraints

- Must publish into the existing template versioning system (ADR-0017) without modification
- Builder output must generate valid Handlebars that the existing template renderer can process
- Budget: 1 designer, 2 engineers for 10 weeks

## Risks

- **Builder-generated HTML quality** may produce templates with poor deliverability if the block renderer generates non-standard markup. Mitigation: use a proven email framework (MJML) as the block rendering engine.
- **Variable schema drift** if marketing adds undeclared variables in template copy. Mitigation: pre-publish validator checks all `{{variable}}` references against the declared schema.

## Milestones

### M1: Builder Canvas and Preview (Weeks 1-5)
#### Deliverables
- Drag-and-drop block editor with all required block types
- Variable picker integrated with notification type variable schema
- Desktop and mobile preview rendering
#### Acceptance Criteria
- All block types functional and renderable
- Variable placeholders resolve correctly in preview
- Mobile preview matches actual Gmail iOS rendering within acceptable tolerance

### M2: Validation, Versioning, and Publishing (Weeks 6-10)
#### Deliverables
- Pre-publish spam score and mobile rendering validation
- Template versioning integration (minor/major version publishing)
- Role-based access control (creator vs. approver)
- Unsubscribe link enforcement validator
#### Acceptance Criteria
- Templates with spam score > 3 are blocked from publishing
- Published templates appear correctly in the template store and can be rendered by the Email Delivery Service
- Marketing users cannot publish without unsubscribe link present
