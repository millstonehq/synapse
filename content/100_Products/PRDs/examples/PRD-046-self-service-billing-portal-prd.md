---
id: PRD-046
type: prd
title: Self-Service Billing Portal PRD
status: approved
owner: Head of Product
created: '2024-01-01T07:58:51.795Z'
updated: '2025-11-22T07:41:14.400Z'
tags:
  - prd
  - billing-engine
summary: Self-Service Billing Portal PRD
related_tdds:
  - TDD-048
  - TDD-047
example: true
related_standards:
  - STANDARD-056
---

## Summary

Build a self-service billing portal that gives customers direct access to their billing history, current subscription details, payment methods, and the ability to perform common billing actions without contacting support. This addresses the current situation where all billing inquiries and changes require a support ticket, resulting in 400+ tickets per month consuming 30% of Customer Success capacity. The portal integrates with the Subscription Management Service ([[TDD-048|TDD-048]]) and Usage Aggregation Service ([[TDD-047|TDD-047]]).

## Goals

- Reduce billing-related support tickets by 60% by enabling customer self-service for common actions
- Increase customer trust in billing accuracy by providing transparent, real-time usage and charge visibility
- Reduce time-to-resolution for billing disputes from 3 days (current) to under 4 hours
- Enable customers to manage payment methods without involving support

## In Scope

- View invoice history with PDF download for each invoice
- View current subscription plan, renewal date, and next invoice estimate
- View current-period usage by metric (API calls, seats, records)
- Update payment method (add new card, set default, remove old)
- Cancel subscription with retention flow (pause offer before cancel)
- Raise a billing dispute with guided evidence collection

## Out of Scope

- Upgrade or downgrade plan (covered in PRD-049 Billing Admin Console)
- Real-time usage alerting / threshold notifications (separate initiative)
- Multi-account / organization billing management
- PO-based enterprise invoicing workflow

## Users and Flows

**Subscription owner** (the account admin who manages billing): This is the primary user. They need to review invoices, update payment methods, understand usage charges, and handle billing disputes. They access the portal from the account settings area and authenticate via the platform's existing SSO.

**Finance staff at customer companies**: Secondary users who need to download invoices and receipts for expense reporting. They typically access the portal via a link from the invoice email. They cannot modify subscription settings — view-only access.

## Requirements

- Display all invoices for the account with date, amount, status, and PDF download link
- Show current subscription plan name, billing period, renewal date, and price
- Show current-period usage broken down by metric with progress toward any plan limits
- Allow adding a new payment method via Stripe Elements (card collection stays in Stripe, not our servers)
- Allow setting a payment method as default and removing unused methods
- Allow initiating a subscription cancellation with a confirmation flow and optional pause offer
- Allow submitting a billing dispute with a free-text description and optional document attachment
- Send email confirmation for all account-modifying actions (payment method change, cancellation initiated)

## KPIs

- **Self-service rate**: 60% of billing inquiries resolved without a support ticket (baseline: 0%)
- **Portal adoption**: 40% of customers visit the portal at least once per billing cycle within 6 months
- **Dispute resolution time**: Median time from dispute submission to resolution < 4 hours
- **Support ticket reduction**: Billing-related support tickets reduce from 400/month to < 160/month

## Information Architecture

- Portal UI lives under `app.example.com/billing`
- Invoice PDFs stored in S3 and served via signed URL with 1-hour expiry
- TDD for Subscription State Machine: [[TDD-048|TDD-048]]
- TDD for Usage Aggregation: [[TDD-047|TDD-047]]
- Portal compliance requirements governed by [[STANDARD-056|STANDARD-056]]

## Data Model

- **PortalSession**: `id`, `customer_id`, `actor_user_id`, `ip_address`, `created_at`, `expires_at` (for audit trail)
- **BillingDispute**: `id`, `customer_id`, `invoice_id`, `description`, `status` (open/under_review/resolved), `submitted_at`, `resolved_at`, `resolution`
- **PortalAuditEvent**: `id`, `session_id`, `action` (view_invoice/update_payment_method/cancel_subscription), `metadata`, `created_at`

## Non-Functional

- Portal must load in under 2 seconds on a standard broadband connection
- All portal actions must be logged to the PortalAuditEvent table for compliance
- Payment method operations must use Stripe Elements to maintain PCI DSS scope exclusion
- Portal must be accessible (WCAG 2.1 AA minimum)

## Constraints

- Payment method tokenization must use Stripe — no alternative card collection mechanism
- Portal authentication must use existing SSO — no separate credential store
- Invoice PDF generation must reuse existing Billing Engine PDF service
- Budget: 3 engineers for 8 weeks (UI + API + integration)

## Risks

- **Cancellation flow increases involuntary churn** if pause offer is not compelling. Mitigation: A/B test pause offer messaging; monitor cancellation-to-pause conversion rate.
- **Dispute tooling creates expectation of automatic credits** Mitigation: clear messaging that disputes are reviewed by a human, not automatically resolved.
- **Portal adoption is low if customers don't know it exists** Mitigation: announce in invoice email footer and in-app billing section from day 1.

## Milestones

### M1: Invoice History and Usage View (Week 1-4)

#### Deliverables

- Invoice list and PDF download functional
- Current-period usage by metric visible
- Current subscription plan and renewal date visible
- Portal authenticated via SSO

#### Acceptance Criteria

- Customer can view all invoices and download PDFs
- Usage display matches Usage Aggregation Service data within 1-hour delay
- Portal loads in under 2 seconds on staging environment

### M2: Payment Method Management and Cancellation (Week 5-8)

#### Deliverables

- Add/remove/set-default payment method via Stripe Elements
- Cancellation flow with pause offer
- Billing dispute submission form
- All portal actions logged to audit table

#### Acceptance Criteria

- Customer can add a card and set it as default without leaving the portal
- Cancellation flow completes without triggering actual cancellation until confirmed
- Dispute submissions appear in the Billing Admin Console for support staff
- All actions produce audit events visible in the admin console
