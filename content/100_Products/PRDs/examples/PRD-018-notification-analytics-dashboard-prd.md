---
id: PRD-018
type: prd
title: Notification Analytics Dashboard PRD
status: draft
owner: Product Manager
created: '2024-06-20T17:42:10.582Z'
updated: '2026-08-13T22:34:35.804Z'
tags:
  - prd
  - notification-service
summary: Notification Analytics Dashboard PRD
related_tdds:
  - TDD-018
  - TDD-019
example: true
related_standards:
  - STANDARD-021
---

## Summary

Build a self-service Notification Analytics Dashboard that gives notification producers visibility into delivery, engagement, and opt-out metrics for their notification types. Currently all analytics reporting requires ad-hoc requests to the Notification Platform team. The dashboard reduces this overhead and enables producers to independently monitor and optimize their notification strategies.

## Goals

- Enable notification producers to self-serve delivery and engagement analytics without engaging the platform team
- Reduce ad-hoc analytics requests to the Notification Platform team by 80%
- Surface actionable insights that help producers improve delivery rates and engagement

## In Scope

- Per-notification-type delivery funnel (dispatched → accepted by provider → delivered → opened)
- Channel performance comparison (email vs. push vs. SMS for the same notification type)
- Opt-out trend tracking per notification type and channel
- Time-series charts with configurable date range (7d, 30d, 90d, custom)
- Drill-down from notification type to individual send events for debugging
- CSV export of metrics data
- Access controlled by notification producer team (each team sees only their own notification types)

## Out of Scope

- User-level analytics (individual user delivery history is available via the notification center, not this dashboard)
- A/B testing framework (separate initiative)
- Predictive analytics or ML-based recommendations
- Real-time streaming dashboards (refresh interval is 15 minutes minimum)

## Users and Flows

**Notification producers** (engineering teams that send notifications via the platform API) are the primary users. They access the dashboard to monitor delivery health for their notification types, investigate delivery failures, and track opt-out trends. A producer sees only the notification types registered under their team's producer ID.

**Notification Platform team** has full dashboard access across all producers for operational monitoring and support escalations.

The typical producer workflow: log into the dashboard, select a notification type, view the 30-day delivery funnel, identify any drops between "dispatched" and "delivered", and drill down to recent failures to identify error patterns.

## Requirements

- Display delivery funnel metrics (dispatched, accepted, delivered, opened) per notification type
- Support date range filtering: last 7 days, 30 days, 90 days, or custom range
- Channel breakdown within each notification type (email, push, SMS proportions and success rates)
- Opt-out rate trend line per notification type
- Error code breakdown for failed deliveries (provider error codes grouped and labeled)
- Drill-down to individual send events with message ID, timestamp, provider, and error code
- CSV export for any metric view
- Access control: producers see only their notification types; platform team sees all

## KPIs

- **Self-service adoption**: > 70% of notification producers use the dashboard at least once per month within 6 months of launch
- **Ad-hoc request reduction**: Reduce platform team ad-hoc analytics requests by 80%
- **Dashboard load time**: Initial dashboard load P95 < 3 seconds

## Information Architecture

- This PRD in `100_Products/PRDs/`
- Batching Service TDD [[TDD-018|TDD-018]] covers the Kafka delivery event pipeline that feeds this dashboard
- Preference API TDD [[TDD-019|TDD-019]] covers opt-out data model relevant to opt-out trend metrics
- Notification analytics data stored in ClickHouse

## Data Model

- **DeliveryEvent**: `eventId`, `notificationId`, `producerId`, `notificationType`, `channel`, `status` (dispatched|accepted|delivered|opened|failed), `errorCode`, `provider`, `timestamp`
- **AggregatedMetrics**: Pre-computed daily aggregates per `(producerId, notificationType, channel)` for fast dashboard queries
- Raw events in ClickHouse; aggregates materialized in ClickHouse materialized views

## Non-Functional

- Dashboard queries must complete within 3 seconds for 90-day date ranges
- ClickHouse cluster sized to handle 30-day query scans across 500M delivery events
- Data freshness: delivery events available in dashboard within 15 minutes of occurrence

## Constraints

- Must use existing ClickHouse infrastructure used by the SMS Dispatch Service
- Dashboard is read-only; no ability to trigger resends or modify notifications from the dashboard
- Budget: 1.5 engineers for 8 weeks

## Risks

- **ClickHouse query performance** for long date ranges across high-volume producers may exceed 3-second target without proper materialized views. Mitigation: pre-compute daily aggregates; limit raw event drill-down to 7-day windows.
- **Access control complexity** for multi-team producers where engineers belong to multiple teams. Mitigation: use explicit producer ID assignment rather than team membership inference.

## Milestones

### M1: Data Pipeline and Core Metrics (Weeks 1-4)
#### Deliverables
- Kafka consumer writing delivery events to ClickHouse
- Materialized views for daily aggregates
- Delivery funnel and channel breakdown views for a single notification type
#### Acceptance Criteria
- Delivery events appear in ClickHouse within 15 minutes of occurrence
- Funnel metrics match data from existing manual SQL queries within 1%
- Dashboard loads in < 3 seconds for 30-day date ranges

### M2: Full Dashboard and Access Control (Weeks 5-8)
#### Deliverables
- Full date range support (7d, 30d, 90d, custom)
- Opt-out trend charts and error code breakdown
- Individual send event drill-down
- CSV export
- Access control with producer ID scoping
#### Acceptance Criteria
- All views load in < 3 seconds
- Producers can only see their own notification types
- CSV export completes within 30 seconds for 90-day exports
