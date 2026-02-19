---
id: PROCESS-049
type: process
title: Customer Feature Request Intake Process
status: approved
owner: Director of Engineering
created: '2024-04-03T09:09:54.903Z'
updated: '2026-02-22T03:43:47.429Z'
tags:
  - process
  - customer-portal
summary: Customer Feature Request Intake Process
related_standards:
  - STANDARD-050
  - STANDARD-054
related_sops:
  - SOP-085
  - SOP-090
related_systems:
  - SYSTEM-044
example: true
---

## Purpose

This process ensures that feature requests submitted by customers through the portal are systematically captured, evaluated, and routed to the appropriate product and engineering backlog. Without a structured intake process, requests get lost in support tickets, duplicated across channels, or acted on inconsistently. This process creates a single path from customer request to prioritized backlog item.

The process applies to requests submitted via the in-portal feedback widget, customer success manager escalations, and direct support ticket requests tagged as feature requests.

## Scope

- Feature requests submitted via the Customer Portal feedback widget
- Requests escalated by customer success managers from customer conversations
- Support tickets reclassified as feature requests during triage
- Bulk feature request patterns identified during monthly feedback analysis

## Roles and Responsibilities

- **Customer Success Manager**: Captures and validates customer context, attaches to request ticket
- **Product Manager**: Triages incoming requests, merges duplicates, assigns priority score
- **Engineering Lead**: Reviews technical feasibility for shortlisted requests, provides effort estimates
- **Portal Support Agent**: Reclassifies support tickets as feature requests during ticket triage

## Triggers

- Customer submits a feature request via the in-portal feedback widget
- Customer success manager logs a feature request from a customer call
- Support agent reclassifies a support ticket as a feature request during triage

## Inputs

- Customer-submitted request text and optional attachment
- Customer account tier and contract details (for priority weighting)
- Related existing tickets or feature requests (for deduplication)

## Outputs

- Deduplicated feature request record in the product backlog tool
- Customer acknowledgment sent within 2 business days
- Prioritized shortlist reviewed by product and engineering in monthly intake meeting

## Steps

1. Customer submits request via the portal feedback widget; system creates a ticket with submitter account details and request text
2. Support agent reviews new requests daily, filters spam and duplicates, and tags tickets as feature requests or support issues
3. Product Manager merges duplicate requests and attaches them to the canonical feature request record
4. Product Manager scores the request against impact criteria (affected customer count, contract tier, strategic alignment)
5. Engineering Lead reviews top-scored requests for technical feasibility and provides a rough effort band (S/M/L/XL)
6. Product Manager adds feasibility-scored requests to the prioritized backlog in the next sprint cycle
7. Customer receives an automated acknowledgment; high-priority requests receive a personalized follow-up from customer success

## Controls

- All feature requests must be logged in the backlog tool within 2 business days of submission
- Requests from enterprise-tier customers must be reviewed by product manager within 5 business days
- Monthly intake review meeting attendance by both product and engineering is required
