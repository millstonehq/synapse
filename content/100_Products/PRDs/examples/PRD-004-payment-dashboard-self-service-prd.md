---
id: PRD-004
type: prd
title: Payment Dashboard Self-Service PRD
status: accepted
owner: Product Manager
created: '2024-02-17T09:29:32.222Z'
updated: '2026-07-01T03:44:38.735Z'
tags:
  - prd
  - payment-processing
summary: Payment Dashboard Self-Service PRD
related_tdds:
  - TDD-003
  - TDD-002
example: true
related_standards:
  - STANDARD-002
---

## Summary

Deliver a self-service payment dashboard that enables operations staff and finance users to manage payment operations without engineering assistance. Currently, all refunds, payment lookups, and reconciliation tasks require an engineer to run database queries or call the API directly. The self-service dashboard exposes these capabilities through a web UI, reducing engineering toil and empowering operations staff to resolve customer issues faster. Related TDDs: [[TDD-003|Payment Webhook Processing Pipeline TDD]] and [[TDD-002|Transaction Retry Engine TDD]].

## Goals

- Reduce engineer time spent on payment operations tasks from ~6 hours/week to < 30 minutes/week
- Enable operations staff to resolve common customer payment issues (refunds, status lookups) without engineering involvement
- Give finance users direct access to transaction exports and reconciliation data
- Reduce mean time to resolve customer payment support tickets from 4 hours to < 30 minutes

## In Scope

- Transaction search and filter by customer, date range, amount, status, and gateway
- Transaction detail view: full payment lifecycle events, gateway response, idempotency key
- Refund initiation: full and partial refunds with reason code and audit trail
- Transaction export: CSV export of filtered results for finance reconciliation
- Role-based access: "Operations" role (search + refund), "Finance" role (search + export, no refund)
- Audit log: all dashboard actions logged with user identity and timestamp

## Out of Scope

- Real-time payment monitoring / alerting (handled by Grafana and PagerDuty)
- Fraud case management (separate tool)
- Chargeback dispute management (separate tool)
- Payment method management on behalf of customers

## Users and Flows

**Operations staff**: Search for a specific customer's payment, view the full event history, initiate a refund. Can resolve most customer issues in under 5 minutes without engineering.

**Finance users**: Search and export transactions by date range for monthly reconciliation. View revenue totals by gateway and currency.

**Engineering on-call**: Uses the detail view to quickly check payment state and gateway response during incident investigation, without needing database access.

## Requirements

- Search transactions by: customer ID, email, payment ID, order ID, date range, amount range, status, gateway
- Display transaction detail: amount, currency, status, created date, gateway, idempotency key, all payment events with timestamps
- Initiate full or partial refund with reason code selection; confirm with a two-step dialog to prevent accidental refunds
- Export current search results to CSV (up to 10,000 rows)
- All dashboard actions must appear in the payment audit log
- Finance role cannot initiate refunds; Operations role cannot export PII

## KPIs

- **Engineer toil reduction**: < 30 minutes/week of engineering time on payment operations tasks (from 6 hours baseline)
- **Support ticket resolution time**: Mean time to resolve payment tickets < 30 minutes (from 4-hour baseline)
- **Dashboard adoption**: 100% of refund operations processed via dashboard within 30 days of launch
- **Audit coverage**: 100% of dashboard actions appear in the payment audit log

## Information Architecture

- This PRD defines the self-service dashboard requirements
- Technical design for webhook processing in [[TDD-003|Payment Webhook Processing Pipeline TDD]]
- Technical design for retry operations in [[TDD-002|Transaction Retry Engine TDD]]

## Data Model

No new entities. Dashboard reads from existing:
- `payments` table for transaction search and detail
- `payment_events` table for full lifecycle history
- New: `dashboard_audit_log` table for recording dashboard actions (refund, export)

## Non-Functional

- Transaction search must return results within 2 seconds for any date range up to 90 days
- Refund action must be idempotent — double-clicking the confirm button does not initiate two refunds
- Dashboard must be accessible only to authenticated employees; no external access
- Audit log writes are synchronous — refund is not confirmed until the audit record is written

## Constraints

- Must use existing authentication service for SSO; no separate login
- Role definitions must be manageable by the security team without code changes
- Must not expose raw card data; last four digits only
- Budget: 1 engineer for 8 weeks

## Risks

- **Accidental refunds** by operations staff unfamiliar with the tool. Mitigation: two-step confirmation dialog; refund reason code required; all refunds appear in daily audit report sent to the manager.
- **PII in CSV exports** if export scope is too broad. Mitigation: Finance role export includes amount, date, status, currency — no customer name or email unless explicitly in scope.
- **Search performance** on the 1.5M+ transaction table. Mitigation: search queries use indexed columns only (customer_id, state, created_at); full-text search is not offered.

## Milestones

### M1: Search and Detail View (Week 1-4)

#### Deliverables

- Transaction search with all filter criteria
- Transaction detail view with full event history
- Role-based access control with Operations and Finance roles

#### Acceptance Criteria

- Operations staff can find any transaction by customer ID within 2 seconds
- Finance users can view transaction history but refund button is hidden

### M2: Refund and Export (Week 5-7)

#### Deliverables

- Refund initiation with two-step confirm and reason code
- CSV export up to 10,000 rows
- Dashboard audit log

#### Acceptance Criteria

- Refund initiated via dashboard appears in transaction events within 10 seconds
- Export of 10,000 transactions completes within 30 seconds
- All refund actions appear in the audit log

### M3: Launch (Week 8)

#### Deliverables

- Rollout to operations team with 2-hour training session
- 30-day monitoring period for audit log completeness

#### Acceptance Criteria

- Operations team can independently process refunds and close tickets
- Engineer escalation for payment operations tasks drops by > 80% within 30 days
