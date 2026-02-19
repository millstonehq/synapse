---
id: MEETING-097
type: meeting
title: Invoice Template Redesign Workshop
status: accepted
owner: Principal Engineer
created: '2025-01-31T17:41:29.612Z'
updated: '2025-10-13T16:20:05.135Z'
tags:
  - meeting
  - billing-engine
summary: Invoice Template Redesign Workshop
company: BillingEngine
topic: Invoice Template Redesign Workshop
meeting_date: '2024-07-07T14:37:22.007Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Billing Engine Platform
- **Topic**: Invoice Template Redesign Workshop
- **Date/Time**: 2024-07-07 14:37 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Workshop to define requirements for the redesigned invoice PDF template. Customer support has escalated 47 support tickets in Q2 about invoice readability and missing information. The current template was designed 3 years ago and does not meet current legal requirements in the EU or accessibility standards.

## Observations by Domain

- **Legal Requirements**: Current invoice template is missing required elements for EU VAT compliance (supplier VAT number, customer VAT number for B2B, VAT rate per line item). A legal review has confirmed this is a compliance issue for EU customers
- **Accessibility**: Invoice PDFs do not meet WCAG 2.1 AA — screen readers cannot parse the table structure. This is a legal requirement in the UK and Germany for B2B invoices
- **Usage Breakdown**: Customers on usage-based plans report difficulty understanding their charges — the current template does not show usage quantities, only the calculated charge per dimension
- **Branding**: The current template uses old brand colors and logo; product team wants alignment with the updated brand guide by Q3

## Key Metrics & Data Points

- **Q2 invoice-related support tickets**: 47 (up from 22 in Q1)
- **EU VAT compliance gap**: VAT number fields and per-line VAT rate missing
- **Usage breakdown requests**: 31 of 47 tickets are customers asking for more usage detail
- **PDF accessibility score**: WCAG audit score 1.8/5 (AA requires 4+)

## Preliminary Scorecard Hooks

- Legal Compliance: 2/5 - EU VAT fields missing; UK accessibility requirement not met
- Customer Clarity: 2/5 - Usage breakdown missing; 31 support tickets from confused customers
- Accessibility: 2/5 - WCAG 2.1 AA not met; remediation required
- Brand Alignment: 2/5 - Template using 3-year-old brand assets

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| EU VAT compliance issue | High | Certain | Tech Lead | Add VAT number fields and per-line VAT rate to template immediately | 2024-07-31 |
| WCAG accessibility non-compliance | High | Certain | Principal Engineer | Rebuild PDF template with accessible table structure | 2024-09-30 |
| Customer confusion over usage invoices | Medium | Certain | Tech Lead | Add usage quantity and unit columns alongside charge column | 2024-08-31 |

## Decisions & Next Steps

### Decisions

- EU VAT compliance fields are P0 and must ship before the August billing cycle
- Full template rebuild (accessibility + brand + usage detail) will ship in September
- Template redesign will use a new PDF rendering library (WeasyPrint) to support accessible table structures

### Action Items

- Tech Lead: Add EU VAT fields (VAT numbers, per-line rate) as a hotfix by 2024-07-25
- Principal Engineer: Evaluate WeasyPrint for PDF rendering, share accessibility test results by 2024-07-21
- Product Manager: Provide updated brand assets and final wireframes for full redesign by 2024-07-28

### Follow-ups

- UAT session with Finance and Customer Support on new template: 2024-08-20
- Customer communication about updated invoice format: 2024-09-01
