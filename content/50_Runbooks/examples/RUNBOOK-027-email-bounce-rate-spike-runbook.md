---
id: RUNBOOK-027
type: runbook
title: Email Bounce Rate Spike Runbook
status: approved
owner: On-Call Engineer
created: '2024-03-14T02:11:02.737Z'
updated: '2025-12-19T06:23:49.219Z'
tags:
  - runbook
  - notification-service
summary: Email Bounce Rate Spike Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / SendGrid / Amazon SES

## Alerts

- `email_bounce_rate_high` - Email bounce rate exceeds 5% over a rolling 10-minute window
- `email_hard_bounce_rate_critical` - Hard bounce rate exceeds 2% — triggers immediate action
- `email_complaint_rate_high` - Spam complaint rate exceeds 0.1% as reported by provider feedback loop
- `email_ip_reputation_warning` - Sending IP reputation score drops below threshold in provider dashboard

## Diagnosis Steps

1. **Determine bounce type composition** - In the SendGrid Activity Feed, filter by bounce events and classify: hard bounces (5.1.x, 5.5.x) indicate invalid or non-existent addresses; soft bounces (4.x.x) indicate temporary delivery failures.
2. **Identify the notification type driving the bounces** - Cross-reference bounce timestamps with the notification type or campaign in the Notification Service logs. A spike from a single campaign indicates a list quality issue.
3. **Check for new address segments** - Determine if the bouncing addresses came from a new user segment, data import, or campaign that used a list not previously validated.
4. **Check for DNS-related delivery failures** - If soft bounces reference DNS errors or relay unavailability for specific domains, check if those receiving domains have outages.
5. **Check sending IP reputation** - In SendGrid's IP Reputation section, verify no blacklisting events or reputation drops have occurred that could be amplifying bounce rates.

## Remediation Steps

1. **If hard bounce rate exceeds 2%**: Immediately bulk-add all hard-bounced addresses to the suppression list using the Handle Email Bounce Storm SOP (SOP-032).
2. **If bounces are concentrated in a single campaign or notification type**: Pause that campaign/type immediately, identify the data source of bad addresses, and do not resume until the list is cleaned.
3. **If the sending IP has been blacklisted**: Reduce send volume immediately, contact SendGrid support, and begin IP reputation recovery process (may require warmup from a new IP).
4. **If complaint rate is elevated**: Audit the recent sends for any opt-out compliance issues; pause marketing sends while investigating; ensure unsubscribe links are functional.
5. **If the issue is transient soft bounces from domain outages**: Allow normal retry behavior for soft bounces; monitor until the receiving domain recovers.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post assessment in #notifications-incidents |
| 15 min | If hard bounce rate critical: page Notification Service Platform Lead immediately |
| 30 min | If IP reputation affected or blacklisting: page Engineering Manager |
| 60 min | Compliance Officer must be notified if complaint rate exceeds 0.3% |

## Dashboards

- [Email Bounce Dashboard](https://grafana.example.com/d/email-bounces) - Bounce rate by type, trend over time
- [Email Reputation Metrics](https://grafana.example.com/d/email-reputation) - Complaint rate, IP reputation score
- [SendGrid Activity Feed](https://app.sendgrid.com/email_activity) - Individual bounce events with error codes
- [Notification Delivery by Type](https://grafana.example.com/d/notification-by-type) - Delivery breakdown by notification event type
