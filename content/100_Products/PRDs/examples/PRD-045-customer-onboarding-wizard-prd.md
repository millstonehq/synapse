---
id: PRD-045
type: prd
title: Customer Onboarding Wizard PRD
status: proposed
owner: Head of Product
created: '2024-10-21T09:49:13.483Z'
updated: '2026-10-21T13:48:30.955Z'
tags:
  - prd
  - customer-portal
summary: Customer Onboarding Wizard PRD
related_tdds:
  - TDD-044
  - TDD-045
example: true
related_standards:
  - STANDARD-054
---

## Summary

Build a guided onboarding wizard that walks new customers through the key portal features — account setup, preferences, their first support ticket, and portal search — during their first login session. The wizard increases time-to-first-value and reduces early-lifecycle support tickets from customers who are confused by the portal. The onboarding experience leverages the search integration from [[TDD-044|TDD-044]] and the real-time notification infrastructure from [[TDD-045|TDD-045]] to demonstrate portal capabilities during the wizard flow.

## Goals

- Reduce support tickets from customers in their first 7 days by 25% (currently the highest-volume ticket category is "how do I...")
- Increase the percentage of customers who complete at least one self-service action in their first session from 38% to 65%
- Increase portal activation rate (customers who log in more than once in the first 14 days) from 55% to 70%
- Achieve a wizard completion rate >= 75% (customers who start the wizard finish all steps)

## In Scope

- Multi-step wizard overlay shown on first login (after email verification)
- Step 1: Welcome and account summary — display account tier and explain the dashboard
- Step 2: Preferences setup — allow customer to set notification preferences during wizard
- Step 3: Submit your first ticket (optional) — guided ticket submission form with pre-populated example fields
- Step 4: Search demo — guided search with a sample query to familiarize the customer with search
- Step 5: Completion — summary of portal capabilities with links to help articles
- Wizard progress persisted: if the customer closes mid-wizard, they can resume where they left off
- "Skip" option on every step except Welcome

## Out of Scope

- Personalized wizard paths based on account type (single path for v1)
- Video tutorials embedded in the wizard
- Wizard re-trigger for returning customers (one-time only)
- Wizard on mobile app (web only for v1; mobile wizard is a future phase)

## Users and Flows

**New customers (first login)**: Customers who have completed email verification and log in for the first time. The wizard is shown as a full-screen overlay on the dashboard.

**Returning new customers** (within first 7 days, wizard not yet completed): The wizard banner is shown at the top of the dashboard with a "Continue your setup" prompt.

## Requirements

- Wizard must be shown to every customer on their first login session, as a step-by-step overlay on the dashboard
- Wizard progress must be persisted in the customer's preferences via the Preference Service; closing the browser and returning must resume from the last completed step
- Each wizard step must have a Skip button (except Step 1) and a Back button
- Step 2 (Preferences) must save notification preferences to the Preference Service when the customer clicks "Save and continue"
- Step 3 (Ticket submission) is optional: the customer can skip it without submitting a ticket
- Step 4 (Search demo) must use the portal search integration and demonstrate a search query result
- Wizard must be completable in under 5 minutes
- Wizard must be keyboard navigable and pass axe-core accessibility tests
- After wizard completion, the customer is redirected to the dashboard with a welcome notification delivered via the notification center

## KPIs

- **Wizard completion rate**: >= 75% of customers who see the wizard complete all steps
- **7-day support ticket rate for new customers**: 25% reduction within 90 days of launch
- **Portal activation rate**: >= 70% of customers log in more than once in their first 14 days
- **First self-service action rate**: >= 65% of new customers complete a portal action in their first session

## Information Architecture

Onboarding documentation:

- This PRD in `100_Products/PRDs/PRD-045` defines the product requirements
- TDD-044 documents the search integration used in Step 4
- TDD-045 documents the real-time update infrastructure used for the completion notification
- A welcome notification template is configured in the Notification Ingestion Service

## Data Model

Onboarding state is stored as customer preferences:

- `onboarding.wizard.status`: `not_started | in_progress | completed`
- `onboarding.wizard.last_step`: integer 1–5 (last completed step)
- `onboarding.wizard.completed_at`: ISO datetime

These are standard Preference key-value pairs persisted by the Preference Service. No new data model is required.

## Non-Functional

- Wizard overlay must not block background page load; the dashboard must fully load behind the wizard
- Wizard must not be shown if the customer's account was created more than 14 days ago (edge case: delayed first login)
- Preference saves during the wizard must not block wizard navigation; save failures must be retried silently
- Wizard must render correctly at 375px (minimum mobile viewport) even though mobile wizard is out of scope (for customers on narrow desktop windows)

## Constraints

- Must use the existing design system component library for all wizard UI
- Must use the Customer API Gateway GraphQL API to save preferences and submit tickets
- Wizard completion notification must use the Notification Center infrastructure (not email)
- Budget: 2 engineers for 6 weeks

## Risks

- **Wizard completion rate below target** if the wizard feels too long. Mitigation: user test the wizard with 5 internal users before launch; target under 4 minutes per user test completion time.
- **Preference save failures** during the wizard could cause the customer to lose progress. Mitigation: show a non-blocking toast for save failures; retry silently up to 3 times; wizard completion re-attempts save on retry.
- **Wizard shown to existing customers** if the `onboarding.wizard.status` preference is not backfilled. Mitigation: run a backfill migration to set `onboarding.wizard.status = completed` for all customers created before the wizard launch date.

## Milestones

### M1: Wizard shell and Step 1-2 (Week 1-2)

#### Deliverables

- Multi-step wizard overlay component
- Step 1: Welcome and account summary
- Step 2: Notification preferences with save to Preference Service
- Wizard progress persistence

#### Acceptance Criteria

- Wizard appears on first login and not on subsequent logins after completion
- Step 2 saves preferences correctly; closing and returning resumes at Step 2
- Wizard is keyboard navigable

### M2: Steps 3-5 and completion (Week 3-4)

#### Deliverables

- Step 3: Optional ticket submission (guided form)
- Step 4: Search demo using the portal search integration
- Step 5: Completion summary with help article links
- Completion notification via the Notification Center

#### Acceptance Criteria

- Step 3 optional ticket creation works end-to-end in staging
- Step 4 search demo returns results via the portal search integration
- Completion notification appears in the portal notification center after wizard close

### M3: Testing and launch (Week 5-6)

#### Deliverables

- User test with 5 internal volunteers; incorporate feedback
- Backfill migration to mark existing customers as wizard-completed
- Staged rollout (new signups only in week 1; all subsequent new signups thereafter)
- Analytics events for wizard_started, wizard_step_completed, wizard_skipped, wizard_completed

#### Acceptance Criteria

- Backfill migration completed with zero wizard triggers for existing customers
- Analytics events fire correctly in staging
- Wizard completion rate >= 70% in first week of data
