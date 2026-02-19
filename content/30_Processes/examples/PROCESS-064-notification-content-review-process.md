---
id: PROCESS-064
type: process
title: Notification Content Review Process
status: deprecated
owner: Engineering Manager
created: '2025-10-12T18:21:10.810Z'
updated: '2025-08-03T18:13:25.160Z'
tags:
  - process
  - notification-service
summary: Notification Content Review Process
related_standards:
  - STANDARD-021
  - STANDARD-023
related_sops:
  - SOP-034
  - SOP-035
related_systems:
  - SYSTEM-018
example: true
---

## Purpose

The Notification Content Review Process ensures that all notification content — email templates, push notification payloads, and SMS message bodies — is reviewed for accuracy, brand compliance, legal requirements, and technical correctness before being published to the production notification system. Without a formal review gate, incorrect or non-compliant notification content can reach millions of users, damage brand trust, and expose the company to regulatory liability under CAN-SPAM, GDPR, or CASL.

This process applies to the creation and publication of new notification templates and to material changes to existing templates. Minor fixes (typos, link corrections) follow an expedited path with single-reviewer approval. New templates and content changes that alter opt-in/opt-out semantics or add new variable requirements require full review.

## Scope

- New email templates submitted to the Notification Template Registry for the first time
- Changes to existing email templates that modify the subject line, body copy, required variable schema, or unsubscribe handling
- New push notification payload definitions (title/body copy and deep link targets)
- New or changed SMS message body templates
- Changes to notification category classifications (e.g., reclassifying a notification from transactional to marketing)

## Roles and Responsibilities

- **Content Author**: The engineer or product manager who creates or modifies the notification content. Responsible for: submitting the content for review, providing the business justification, completing the pre-submission checklist, and addressing reviewer feedback.
- **Technical Reviewer**: An engineer from the Notification Platform team. Responsible for: verifying template variable schema correctness, confirming unsubscribe link presence for email, validating that push payload does not exceed platform size limits, and approving via the template registry review UI.
- **Compliance Reviewer**: The Engineering Manager or a designated compliance-aware engineer. Required for any content classified as marketing. Responsible for: verifying CAN-SPAM/GDPR compliance, confirming opt-out scope is correct, and approving the content category classification.
- **Approver**: Product Manager for the owning feature area. Provides final sign-off that the content matches the product intent and has been reviewed by legal if required.

## Triggers

- A pull request adds a new template file to the notification template source repository
- A content author submits a template change request ticket referencing an existing template slug
- A notification type classification change (transactional → marketing or vice versa) is proposed
- The Notification Platform team's quarterly template audit identifies content that has not been reviewed under this process

## Inputs

- Draft notification content (template source file or push/SMS payload JSON) with proposed variable schema
- Business justification describing why the notification exists and which users will receive it
- The notification type and category classification (transactional or marketing)
- For email: confirmation that the unsubscribe link and physical address footer are present
- For marketing content: confirmation that recipients have opted in to the relevant category

## Outputs

- Published template in the [[SYSTEM-018|Push Notification Gateway]] template registry (for push payloads) or the Email Template Registry (for email)
- Completed review record in the content review tracking system with reviewer names, approval timestamps, and any compliance notes
- Updated notification type registry entry if category classification changed
- Notification to the submitting team confirming publication and the live template slug and version

## Steps

1. **Content Author** completes the pre-submission checklist per [[SOP-034|Notification Producer Onboarding SOP]]: confirms variable schema is documented, unsubscribe link is present (email), content does not contain prohibited language (per [[STANDARD-021|Notification Content Standards]]), and the notification type is registered
2. **Content Author** opens a review request in the template review tracking system, attaching the draft content, variable schema, business justification, and classification
3. **Technical Reviewer** (Notification Platform engineer) runs the automated pre-publish validator against the template: checks unsubscribe link token format, validates all declared variables are present in the sample variable map, and verifies the template renders without errors for the declared locales
4. **Technical Reviewer** approves or requests changes. If changes are requested, the Content Author revises and resubmits. The technical review step repeats until approved
5. **Compliance Reviewer** reviews marketing-classified content for CAN-SPAM/GDPR compliance per [[STANDARD-023|Notification Delivery Standards]]: confirms opt-in scope, unsubscribe handling, sender identity, and physical address. Transactional content skips this step
6. **Approver** (Product Manager) provides final sign-off confirming the content matches the approved product specification
7. **Content Author** publishes the template to production using [[SOP-035|Email Template Publishing SOP]] (for email) or the push payload registry API (for push/SMS). The publish action is gated on all required approvals being recorded in the review system
8. **Technical Reviewer** verifies the published template in the staging environment sends correctly to a test recipient before the Content Author closes the review ticket

## Controls

- The pre-publish validator (automated) blocks publication of any email template missing the unsubscribe link or physical address footer
- Marketing-classified templates require Compliance Reviewer sign-off before the publish step is unlocked in the template registry
- All review records are retained for 24 months to support compliance audits and DSAR responses
- Template version history is immutable: published template versions cannot be edited, only superseded by a new version following this process
- Quarterly template audits (run by the Notification Platform team) identify templates that have not been reviewed within 12 months and flag them for re-review or deprecation
