---
id: MEETING-035
type: meeting
title: SMS Provider Evaluation Meeting
status: review
owner: Product Manager
created: '2025-04-26T00:29:39.518Z'
updated: '2025-01-06T08:33:10.520Z'
tags:
  - meeting
  - notification-service
summary: SMS Provider Evaluation Meeting
company: NotificationService
topic: SMS Provider Evaluation Meeting
meeting_date: '2025-10-07T00:08:22.572Z'
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

- **Project**: Notification Service - SMS Provider Evaluation
- **Topic**: SMS Provider Evaluation Meeting
- **Date/Time**: 2025-10-07 00:08 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Current primary SMS provider (Twilio) experienced two major outages in the past 6 months. The team is evaluating whether to add a secondary provider or switch primaries.

## Observations by Domain

- **Twilio Reliability**: Twilio had 94.7% uptime for SMS delivery over the past 6 months (two incidents lasting 3h and 5h respectively), below the 99.5% SLA target
- **Vonage as Secondary**: Vonage was evaluated as a secondary provider; integration effort is estimated at 3 engineer-days due to existing abstract provider interface in the Notification Service
- **Bandwidth.com**: Evaluated as an alternative primary; offers lower per-message cost but US-only coverage limits global SMS capability
- **Provider API Compatibility**: All three providers support E.164 format, status webhooks, and 2-way messaging; switching cost is low given the existing abstraction layer
- **Cost Comparison**: Twilio: $0.0079/SMS, Vonage: $0.0065/SMS, Bandwidth: $0.0055/SMS (US only)

## Key Metrics & Data Points

- **Twilio 6-month uptime**: 94.7% — two outages impacting MFA and security alert SMS
- **MFA SMS volume**: 180,000 messages/month — highest priority SMS type
- **Vonage integration estimate**: 3 engineer-days
- **Cost savings with Vonage as primary**: ~$210/month at current volume
- **Global SMS requirement**: 23% of users are outside the US, ruling out Bandwidth as sole provider

## Preliminary Scorecard Hooks

- Twilio Current Performance: 2/5 - Two significant outages in 6 months, below SLA
- Vonage as Secondary: 4/5 - Low integration cost, competitive pricing, good global coverage
- Bandwidth as Primary: 2/5 - Best price but US-only coverage is disqualifying
- Failover Architecture Readiness: 4/5 - Abstract provider interface makes multi-provider easy
- Cost Optimization Opportunity: 3/5 - Modest savings available, not a primary driver

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Vonage integration introduces its own reliability risk | Medium | Low | Tech Lead | Run Vonage in shadow mode for 2 weeks before enabling as failover | 2025-11-01 |
| MFA SMS unavailability during Twilio outage blocks logins | High | Medium | Principal Engineer | Prioritize Vonage as active secondary, not just passive backup | 2025-10-31 |

## Decisions & Next Steps

### Decisions

- Vonage will be onboarded as an active secondary SMS provider, not a cold standby
- Twilio remains primary; automatic failover to Vonage will trigger on 5-minute P95 > 10s
- Bandwidth will not be pursued due to global coverage limitation

### Action Items

- Tech Lead to begin Vonage integration following Notification Channel Onboarding Process (due 2025-10-21)
- Principal Engineer to define automatic failover trigger thresholds (due 2025-10-14)
- Product Manager to communicate SMS provider diversification to customer success team (due 2025-10-10)

### Follow-ups

- Review Vonage shadow mode metrics before enabling as active failover
- Re-evaluate provider mix in 12 months based on reliability data
