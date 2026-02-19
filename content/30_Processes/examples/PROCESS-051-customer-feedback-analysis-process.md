---
id: PROCESS-051
type: process
title: Customer Feedback Analysis Process
status: approved
owner: Platform Lead
created: '2024-05-06T18:23:38.626Z'
updated: '2025-09-18T00:43:57.734Z'
tags:
  - process
  - customer-portal
summary: Customer Feedback Analysis Process
related_standards:
  - STANDARD-052
  - STANDARD-049
related_sops:
  - SOP-081
  - SOP-086
related_systems:
  - SYSTEM-043
example: true
---

## Purpose

This process defines how customer feedback collected through the portal is aggregated, categorized, and translated into actionable insights for product and engineering teams. Ad hoc review of individual feedback items is insufficient at scale; structured analysis surfaces recurring themes, measures sentiment trends, and ensures customer pain points drive roadmap decisions.

## Scope

- In-portal feedback widget submissions
- NPS survey responses collected after key portal actions (account setup, ticket resolution)
- Support ticket data tagged for feedback analysis
- Session replay and analytics signals supplementing qualitative feedback

## Roles and Responsibilities

- **Data Analyst**: Aggregates raw feedback data, runs sentiment classification, and produces the monthly analysis report
- **Product Manager**: Reviews analysis report, identifies themes, and updates roadmap priorities based on findings
- **Platform Lead**: Reviews technical themes (performance, reliability, UX friction) and creates engineering investigation tickets
- **Customer Success Manager**: Provides qualitative context on top customer concerns identified in account reviews

## Triggers

- Monthly on the first business day of each month (scheduled analysis cycle)
- NPS score drops more than 10 points week-over-week (triggered analysis)
- A major portal incident occurs (post-incident feedback collection)

## Inputs

- Raw feedback submissions export from portal feedback system
- NPS survey response data export
- Support ticket volume and category breakdown
- Session analytics data for pages with high exit rates or error events

## Outputs

- Monthly feedback analysis report with sentiment scores and top themes
- Prioritized list of product and engineering action items
- Updated NPS trend dashboard
- Roadmap influence log documenting decisions driven by feedback

## Steps

1. Data Analyst exports feedback data from all sources for the previous month
2. Data Analyst runs sentiment classification and groups submissions into themes (performance, UX, missing features, billing, errors)
3. Data Analyst calculates NPS delta and highlights accounts with negative scores for customer success follow-up
4. Data Analyst publishes draft report in the shared analysis workspace
5. Product Manager reviews report, annotates roadmap implications, and schedules feedback review meeting
6. Platform Lead extracts technical themes and creates investigation tickets in the engineering backlog
7. Feedback review meeting is held; decisions and action items are documented
8. Product Manager updates the roadmap influence log with decisions driven by the analysis

## Controls

- Feedback analysis report must be published within 5 business days of month end
- Engineering tickets created from feedback must be triaged within the same sprint cycle
- NPS trend dashboard must be updated monthly with the latest scores
