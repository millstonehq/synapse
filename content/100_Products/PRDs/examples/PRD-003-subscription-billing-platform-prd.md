---
id: PRD-003
type: prd
title: Subscription Billing Platform PRD
status: approved
owner: Product Manager
created: '2024-10-22T06:54:23.508Z'
updated: '2025-12-25T05:30:09.795Z'
tags:
  - prd
  - payment-processing
summary: Subscription Billing Platform PRD
related_tdds:
  - TDD-004
  - TDD-003
example: true
related_standards:
  - STANDARD-003
---

## Summary

Build a subscription billing platform that enables the product to offer recurring payment plans to customers. Currently all payments are one-time transactions. Subscription billing will unlock SaaS-style pricing, annual plan discounts, and predictable revenue for the business. The platform handles plan creation, subscription enrollment, renewal billing, dunning (failed payment retries), and cancellation. It integrates with the existing Payments API for the actual charge operations. Related TDDs: [[TDD-004|Multi-Currency Support TDD]] and [[TDD-003|Payment Webhook Processing Pipeline TDD]].

## Goals

- Enable recurring billing for monthly and annual plans with automated renewal
- Reduce involuntary churn by 20% through a smart dunning process with 3-attempt retry cadence
- Provide customers with a self-service subscription management page (upgrade, downgrade, cancel)
- Generate predictable monthly recurring revenue (MRR) reporting for the finance team

## In Scope

- Subscription plan management (create, update, deprecate plans)
- Customer subscription enrollment with stored payment method
- Automated renewal billing via cron job (monthly and annual cycles)
- Dunning: 3 retry attempts over 7 days for failed renewals, then subscription suspension
- Customer self-service: view current plan, update payment method, cancel
- Subscription lifecycle events published to SQS for notifications and analytics
- MRR and churn reporting in the analytics dashboard

## Out of Scope

- Usage-based billing (metered subscriptions — v2)
- Proration for mid-cycle plan changes (v2)
- Invoice generation (separate initiative)
- Free trial management (v2)

## Users and Flows

**Customers**: Enroll in a plan at checkout, are billed automatically each cycle, can manage their subscription from their account page. Receive email notifications for successful renewals, failed payments, and upcoming cancellation.

**Finance team**: Monitor MRR, churn rate, and dunning success rate from the analytics dashboard.

**Operations staff**: Can view and manually retry failed renewal attempts. Can cancel subscriptions on behalf of customers.

## Requirements

- Store subscription state machine: `active`, `past_due`, `suspended`, `cancelled`
- Charge stored payment method automatically at renewal date using the existing Payments API
- Retry failed renewals 3 times: at T+1 day, T+3 days, T+7 days. Suspend after 3 failures.
- Send email notifications for: renewal success, renewal failure (with retry schedule), final suspension warning, cancellation confirmation
- Allow customers to update the payment method on an active subscription
- Allow customers to cancel: immediate cancellation or cancel at end of current period
- Publish `subscription.renewed`, `subscription.failed`, `subscription.cancelled` events to SQS

## KPIs

- **Renewal success rate**: > 94% of scheduled renewals succeed on the first attempt
- **Dunning recovery rate**: > 60% of initially failed renewals recovered within the 7-day dunning window
- **Involuntary churn reduction**: 20% reduction in involuntary churn within 90 days
- **Self-service cancellation rate**: > 80% of cancellations completed by customers without support ticket

## Information Architecture

- This PRD defines subscription billing requirements
- Technical design for webhook processing in [[TDD-003|Payment Webhook Processing Pipeline TDD]]
- Multi-currency subscription pricing design in [[TDD-004|Multi-Currency Support TDD]]

## Data Model

New entities:
- **SubscriptionPlan**: `id`, `name`, `amount`, `currency`, `interval` (monthly/annual), `status`
- **Subscription**: `id`, `customer_id`, `plan_id`, `payment_method_id`, `status`, `current_period_start`, `current_period_end`, `cancelled_at`
- **RenewalAttempt**: `id`, `subscription_id`, `payment_id`, `attempt_number`, `status`, `attempted_at`

## Non-Functional

- Renewal batch job must process 10,000 subscriptions within 30 minutes (planned scale)
- Failed renewal retry schedule must be stored durably (survives pod restart)
- Subscription state changes must be idempotent (Stripe webhook retry safety)
- Data retention: subscription records retained for 7 years per financial regulations

## Constraints

- Must use existing Payments API for all charge operations — no direct gateway calls from the subscription service
- Must integrate with existing notification service for customer emails
- Budget: 3 engineers for 12 weeks

## Risks

- **Renewal batch job timing** — if the batch runs long, some customers may be billed late. Mitigation: batch is idempotent; late billing is acceptable if same-day.
- **Payment method expiry** not detected until renewal fails. Mitigation: send "card expiring soon" notification 30 days before renewal when card expiry is within 45 days.
- **Dunning complexity** — 3-attempt retry logic with notifications creates a complex state machine. Mitigation: dedicated dunning state machine with event sourcing; comprehensive test suite.

## Milestones

### M1: Core Subscription Engine (Week 1-5)

#### Deliverables

- Subscription plan and subscription data model
- Enrollment, renewal batch job, and cancellation flows
- SQS event publishing for subscription lifecycle

#### Acceptance Criteria

- Can enroll a test customer in a monthly plan and observe automatic renewal at T+30 days in staging
- Cancellation at end of period correctly stops renewal

### M2: Dunning and Notifications (Week 6-9)

#### Deliverables

- Dunning retry engine with 3-attempt cadence
- Email notifications for all subscription lifecycle events
- Customer self-service subscription management page

#### Acceptance Criteria

- Failed renewal retried correctly at T+1, T+3, T+7; subscription suspended after 3 failures
- Customer can update payment method and trigger immediate retry

### M3: Reporting and Launch (Week 10-12)

#### Deliverables

- MRR and churn metrics in the analytics dashboard
- Load test: 10,000 subscription renewals in < 30 minutes
- Staged rollout to first 500 customers

#### Acceptance Criteria

- MRR report accurate to within 0.1% of manual calculation
- Renewal batch completes within 30-minute SLA
- No SEV-2 incidents during first 2 weeks of rollout
