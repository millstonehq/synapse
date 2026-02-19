---
id: PRD-041
type: prd
title: Customer Self-Service Portal PRD
status: accepted
owner: Senior PM
created: '2025-12-30T04:23:04.112Z'
updated: '2025-10-03T18:09:54.980Z'
tags:
  - prd
  - customer-portal
summary: Customer Self-Service Portal PRD
related_tdds:
  - TDD-041
  - TDD-043
example: true
related_standards:
  - STANDARD-049
---

## Summary

Build a comprehensive self-service portal that enables customers to independently manage their account, submit and track support tickets, update preferences, and access account history without requiring intervention from support staff. This initiative replaces a high-friction experience where basic account tasks require contacting support, consuming significant support team capacity. Technical implementation is guided by [[TDD-041|TDD-041]] (dashboard) and [[TDD-043|TDD-043]] (settings API).

## Goals

- Reduce tier-1 support ticket volume by 30% by enabling customers to self-serve common account management tasks
- Increase Customer Satisfaction Score from 4.1 to 4.5 by reducing time-to-resolution for common requests
- Reduce average support handling time per customer account query from 8 minutes to under 1 minute (deflected to self-service)
- Provide a scalable portal foundation that can accommodate new self-service capabilities each quarter

## In Scope

- Account overview dashboard with open ticket count, notification count, and account tier
- Support ticket submission and tracking (view status, add comments, upload attachments)
- Preference and notification settings management (communication opt-ins, notification categories)
- Account profile editing (display name, email, language, timezone)
- Activity history with search and filtering
- Password change and MFA enrollment

## Out of Scope

- Billing and invoice management (separate initiative)
- Subscription cancellation or plan changes (requires sales-assisted flow)
- Live chat with a support agent (chat integration is a separate PRD)
- Mobile native application (separate PRD)

## Users and Flows

**Authenticated customers**: The primary users. Customers who have signed up and completed email verification. They access the portal at `portal.company.com` and authenticate via the existing SSO flow.

**Support staff (read-only)**: Customer Success Managers can view the portal as a customer to reproduce issues. They do not submit tickets or change preferences on behalf of customers.

## Requirements

- Display account overview with open tickets, unread notifications, and account tier on first load within 2 seconds (P95)
- Allow customers to create support tickets with a subject, description, and up to 3 file attachments (max 5 MB each)
- Allow customers to view all their tickets, filter by status (open, pending, closed), and add comments to open tickets
- Allow customers to update display name, email, preferred language, and timezone
- Allow customers to enable or disable notification categories (ticket updates, system alerts, promotions)
- Allow customers to change their password with current-password confirmation
- Allow customers to enable TOTP-based MFA
- All page loads complete first meaningful paint within 2.5 seconds on a 3G connection

## KPIs

- **Self-service deflection rate**: 30% reduction in tier-1 support tickets within 90 days of launch
- **Portal CSAT**: Average session satisfaction rating >= 4.3 / 5.0
- **Task completion rate**: >= 85% of customers who begin a self-service task complete it without contacting support
- **First meaningful paint**: <= 2.5 seconds P95 on 3G
- **Accessibility**: Zero WCAG 2.2 Level A or AA violations in monthly automated audit

## Information Architecture

Portal documentation spans:

- System docs in `70_Systems/` for the five portal services
- TDDs in `90_Architecture/TDDs/` for dashboard, notification center, and settings API technical designs
- Runbook in `50_Runbooks/` for portal incident response
- This PRD in `100_Products/PRDs/` defining product requirements

## Data Model

Core customer-facing entities:

- **CustomerProfile**: `{ displayName, email, language, timezone, accountTier, memberSince }`
- **SupportTicket**: `{ id, subject, status, createdAt, updatedAt, comments: [TicketComment] }`
- **TicketComment**: `{ id, body, authorType (customer|agent), createdAt }`
- **Preference**: `{ key, value, updatedAt }` — typed preference key-value pairs

Relationships:
- Customer has many SupportTickets (1:N)
- SupportTicket has many TicketComments (1:N)
- Customer has many Preferences (1:N), keyed by preference type

## Non-Functional

- All pages must be server-side rendered for initial load; no blank page flash on navigation
- Authentication state must be validated on every server-side render; unauthenticated requests redirect to login
- Customer data must be scoped strictly to the authenticated customer; no cross-customer data exposure
- Portal must meet WCAG 2.2 Level AA conformance
- All API mutations must emit audit events to the portal event bus

## Constraints

- Must use the existing Customer API Gateway (GraphQL) as the API layer; no direct frontend calls to backend services
- Must deploy on Vercel; backend services remain on Kubernetes
- Team budget: 4 engineers for 12 weeks
- Must reuse the existing design system component library for all UI components

## Risks

- **Settings API integration latency** from two downstream services (Preference Service and Identity Service) could delay settings page load. Mitigation: parallel resolver fetches with a 3-second timeout and per-group graceful degradation.
- **Support ticket volume increase** during launch if self-service reveals previously suppressed customer frustration. Mitigation: staged rollout (10% of customers in week 1); monitor support volume daily.
- **Accessibility regressions** during rapid feature development. Mitigation: run automated axe-core tests in CI on every PR; block merge on any new Level A or AA violation.

## Milestones

### M1: Dashboard and Profile (Week 1-4)

#### Deliverables

- Account overview dashboard with StatCards and ActivityFeed
- Profile settings form (display name, email, language, timezone)
- End-to-end authenticated session management

#### Acceptance Criteria

- Dashboard loads in < 2s P95 from Vercel edge
- Profile updates saved and reflected within one page reload
- All dashboard components pass axe-core accessibility tests

### M2: Ticket Management (Week 5-8)

#### Deliverables

- Ticket list with status filter and pagination
- Ticket creation form with file attachment support
- Ticket detail view with comment thread

#### Acceptance Criteria

- Customer can create a ticket and receive a ticket ID confirmation
- Customer can add a comment to an open ticket
- Ticket list filters by status correctly
- File attachments up to 5 MB accepted; larger files rejected with a clear error

### M3: Settings and Security (Week 9-12)

#### Deliverables

- Notification and communication preferences forms
- Password change flow
- MFA enrollment (TOTP) flow
- Full accessibility audit and remediation

#### Acceptance Criteria

- Notification preferences saved and immediately reflected in notification delivery
- Password change requires current password confirmation
- MFA enrollment completes with a TOTP scan and backup code display
- Zero WCAG 2.2 Level A or AA violations in final audit
