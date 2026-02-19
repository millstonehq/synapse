---
id: PROCESS-019
type: process
title: Notification Template Approval Process
status: draft
owner: Director of Engineering
created: '2024-06-07T04:39:52.379Z'
updated: '2026-09-05T12:00:12.728Z'
tags:
  - process
  - notification-service
summary: Notification Template Approval Process
related_standards:
  - STANDARD-020
  - STANDARD-024
related_sops:
  - SOP-035
  - SOP-039
related_systems:
  - SYSTEM-019
example: true
---

## Purpose

This process ensures that all notification templates are reviewed for content accuracy, compliance, and technical correctness before being deployed to production. Unreviewed templates risk violating opt-out laws, damaging sender reputation, or exposing users to poorly formatted or incorrect messages.

## Scope

- All new notification templates across email, push, SMS, and in-app channels
- Modifications to existing templates that change content, layout, or dynamic variable usage
- Template deletions that affect active notification flows

## Roles and Responsibilities

- **Template Author**: Creates or modifies the template, fills out the review request, and addresses feedback from reviewers
- **Content Reviewer**: Reviews template copy for accuracy, brand voice, and compliance with opt-out and privacy requirements
- **Engineer Reviewer**: Validates template code against [[STANDARD-020|Email Template Coding Standard]] and [[STANDARD-024|In-App Message Format Standard]]
- **Notification Service Team Lead**: Provides final approval for high-risk or cross-channel templates before deployment

## Triggers

- A product team requests a new notification template for a feature
- An existing template requires content or layout changes
- A compliance or legal review flags a template for correction

## Inputs

- Draft template file (HTML, text, or JSON schema depending on channel)
- Description of the notification event that triggers this template
- List of dynamic variables used and their data sources

## Outputs

- Approved template stored in the template registry with version number
- Review record documenting approvals and any changes made
- Deployment ticket linking the approved template to the target notification event

## Steps

1. Template Author creates a draft template following the relevant coding standard and submits a review request in the template management system
2. Content Reviewer assesses the template copy for clarity, accuracy, brand compliance, and presence of required elements (unsubscribe link for non-transactional email)
3. Engineer Reviewer validates the template against the applicable technical standard, checking escaping, layout compatibility, and variable binding
4. Template Author addresses all review feedback and resubmits if changes were required
5. Team Lead reviews and approves templates flagged as high-risk (new compliance-sensitive flows, cross-channel campaigns)
6. Approved template is merged to the template registry under a new version tag
7. Template Author creates a deployment ticket referencing the approved version and links it to the relevant notification event configuration

## Controls

- No template may be deployed to production without a completed review record
- Templates touching opt-out or consent flows require explicit Team Lead sign-off
- Template registry versions are immutable; edits require a new version submission
- All approved templates are retained in the registry for a minimum of 12 months
