---
id: PRD-049
type: prd
title: Billing Admin Console PRD
status: approved
owner: Senior PM
created: '2025-03-07T07:33:40.893Z'
updated: '2026-03-20T06:21:57.654Z'
tags:
  - prd
  - billing-engine
summary: Billing Admin Console PRD
related_tdds:
  - TDD-049
  - TDD-048
example: true
related_standards:
  - STANDARD-060
---

## Summary

Build an internal Billing Admin Console for Customer Success and Finance teams to view, manage, and correct billing data across all customer accounts. Today, billing operations require direct database queries and Stripe dashboard access to perform routine actions such as issuing manual credits, adjusting subscription plans, viewing a customer's billing history, and resolving proration disputes. The Admin Console consolidates these workflows into a purpose-built internal tool. It integrates with the Proration Calculator ([[TDD-049|TDD-049]]) and Subscription State Machine ([[TDD-048|TDD-048]]). Access controls are governed by [[STANDARD-060|STANDARD-060]].

## Goals

- Eliminate the need for Customer Success to use direct Stripe dashboard access or raw SQL queries for billing operations
- Reduce time-to-resolution for billing corrections from 2 days to under 2 hours
- Create a full audit trail for all admin-initiated billing changes
- Enable Finance to run reconciliation and credit note workflows without engineering involvement

## In Scope

- Customer account search and billing history view
- Subscription plan change (upgrade/downgrade) with proration preview
- Manual credit issuance (credit note against future invoice)
- Invoice void and re-issue workflow
- Billing dispute queue and resolution workflow
- Audit log of all admin actions with actor, timestamp, and before/after state

## Out of Scope

- Revenue reporting and forecasting (covered in PRD-050)
- Customer-facing portal (covered in PRD-046)
- Automated credit policies or dunning logic
- Bulk account migrations

## Users and Flows

**Customer Success Representative**: Primary user. They look up a customer account, review the billing history to understand the issue, issue a credit or change the subscription plan as appropriate, and close the support ticket. They need to see a full history of all previous admin actions on the account to avoid duplicate corrections.

**Finance team member**: Uses the console to view the credit note queue, approve large credits (above $500), and run month-end reconciliation checks. They need a view that aggregates credits and adjustments by account and period for reconciliation against the double-entry ledger.

## Requirements

- Search customers by email, account name, or Stripe customer ID
- View a customer's full invoice history with payment status for each invoice
- View a customer's subscription history including all state transitions with timestamps
- Initiate a subscription plan change with real-time proration preview showing expected credit and debit amounts
- Issue a manual credit (credit note) up to the CS rep's authorization limit; credits above $500 require Finance approval
- Void an unpaid invoice and optionally re-issue a corrected version
- View all open billing disputes submitted via the self-service portal with resolution workflow
- All admin actions write to an append-only audit log with actor, IP address, action type, and before/after values

## KPIs

- **Time-to-resolution**: Median billing correction time decreases from 2 days to under 2 hours within 90 days
- **Engineering escalations**: Billing operations requiring engineering intervention decrease by 80%
- **Audit completeness**: 100% of admin billing actions are captured in the audit log (measured by periodic sampling)
- **Finance approval SLA**: Finance-required credit approvals completed within 4 business hours

## Information Architecture

- Admin Console hosted at `admin.example.com/billing` (internal, VPN-required)
- Proration preview uses the Proration Calculator API
- Subscription changes invoke the Subscription State Machine API
- TDD: [[TDD-049|TDD-049]] (Proration Calculator), [[TDD-048|TDD-048]] (Subscription State Machine)
- Access control requirements: [[STANDARD-060|STANDARD-060]]

## Data Model

- **AdminAction**: `id`, `actor_user_id`, `actor_role`, `action_type`, `target_entity_type`, `target_entity_id`, `before_state` (JSON), `after_state` (JSON), `ip_address`, `created_at`
- **CreditNote**: `id`, `account_id`, `invoice_id` (nullable), `amount_cents`, `reason`, `status` (pending_approval/approved/applied), `created_by`, `approved_by`, `applied_at`

## Non-Functional

- Admin Console must be accessible only from the corporate VPN
- All actions must require re-authentication after 30-minute idle session
- Audit log entries must be immutable — no update or delete operations on audit records
- Page load for customer billing history must complete in under 2 seconds for accounts with up to 10 years of invoices

## Constraints

- Must use existing corporate SSO with role-based access (CS Rep vs Finance Approver)
- Must not expose raw Stripe API keys or webhook secrets in the UI
- All credit amounts must be validated against authorization limits before executing
- Budget: 2 engineers for 10 weeks

## Risks

- **Unauthorized credit issuance** if role-based access controls are misconfigured. Mitigation: implement and test RBAC on every action endpoint; include authorization tests in CI.
- **Audit log gaps** if admin actions bypass the console and use direct API calls. Mitigation: deprecate direct Stripe dashboard access for CS reps; enforce all billing changes go through the console.

## Milestones

### M1: Customer Search and History (Week 1-4)

#### Deliverables

- Customer search by email, name, Stripe ID
- Invoice history with payment status
- Subscription state history with timestamps
- Audit log viewer for previous admin actions on the account

#### Acceptance Criteria

- Customer search returns results in under 1 second
- Invoice history shows all invoices with correct payment status
- All fields are read-only in M1 (no mutations yet)

### M2: Plan Changes, Credits, and Dispute Resolution (Week 5-10)

#### Deliverables

- Subscription plan change with proration preview
- Credit note issuance with Finance approval workflow for credits > $500
- Invoice void and re-issue
- Billing dispute queue with resolution workflow
- All admin actions logged to audit table

#### Acceptance Criteria

- Plan change proration preview matches the Proration Calculator output
- Credits above $500 are blocked until Finance approves in the console
- All admin actions appear in the audit log within 5 seconds of execution
