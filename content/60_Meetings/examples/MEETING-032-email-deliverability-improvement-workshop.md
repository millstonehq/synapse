---
id: MEETING-032
type: meeting
title: Email Deliverability Improvement Workshop
status: deprecated
owner: Product Manager
created: '2025-03-16T12:47:17.415Z'
updated: '2026-11-13T19:37:06.546Z'
tags:
  - meeting
  - notification-service
summary: Email Deliverability Improvement Workshop
company: NotificationService
topic: Email Deliverability Improvement Workshop
meeting_date: '2025-04-22T12:37:31.833Z'
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

- **Project**: Notification Service - Email Deliverability Improvement
- **Topic**: Email Deliverability Improvement Workshop
- **Date/Time**: 2025-04-22 12:37 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Following a bounce rate spike in Q1, the team convened to identify deliverability gaps and prioritize improvements before the Q2 campaign push.

## Observations by Domain

- **Email Authentication**: DKIM and SPF are passing but DMARC policy is still in `p=none` monitoring mode; enforcement has not been enabled due to uncertainty about forwarding impacts
- **List Hygiene**: No systematic list validation is in place; addresses from older imports have not been validated, contributing to hard bounce rate above 3%
- **IP Warmup**: The secondary sending IP was never formally warmed up; when used as a failover, it sent at high volume from cold and triggered ISP filtering
- **Bounce Handling**: Hard bounces are being suppressed correctly but soft bounce retry strategy is too aggressive, causing legitimate deferrals to accumulate into hard bounces
- **Unsubscribe Compliance**: One-click unsubscribe via List-Unsubscribe header is implemented but the feedback loop webhook from Yahoo Mail is not configured

## Key Metrics & Data Points

- **Hard bounce rate (Q1 average)**: 3.4% — above the 2% policy threshold
- **Soft bounce rate**: 6.1% — above the 5% policy threshold
- **Spam complaint rate**: 0.08% — within threshold but trending upward
- **DMARC enforcement**: p=none (monitoring only, not enforcing)
- **Secondary IP warmup completion**: 0% — never warmed

## Preliminary Scorecard Hooks

- Email Authentication: 3/5 - DKIM/SPF passing, DMARC monitoring only, needs enforcement
- List Hygiene: 2/5 - No proactive validation, bounce rate above threshold
- IP Warmup Readiness: 1/5 - Secondary IP never warmed, risk to failover scenarios
- Bounce Handling: 3/5 - Hard bounce suppression working, soft bounce retry too aggressive
- Compliance Coverage: 3/5 - List-Unsubscribe present, Yahoo feedback loop missing

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Secondary IP causes blacklisting during failover | High | High | Platform Lead | Begin IP warmup schedule for secondary IP immediately | 2025-05-15 |
| DMARC p=none means no protection against domain spoofing | High | Medium | Tech Lead | Move DMARC to p=quarantine after 30-day monitoring review | 2025-05-30 |
| Hard bounce rate triggers SendGrid account review | Medium | Medium | Principal Engineer | Implement address validation at point of collection | 2025-06-01 |

## Decisions & Next Steps

### Decisions

- DMARC will be moved to `p=quarantine` after a 30-day review period confirms no legitimate mail is failing
- Address validation will be added to the user registration flow to prevent invalid emails from entering the system
- Secondary IP warmup schedule will begin immediately with a 6-week plan

### Action Items

- Tech Lead to draft DMARC enforcement migration plan (due 2025-04-29)
- Principal Engineer to evaluate email validation library options for registration flow (due 2025-05-06)
- Platform Lead to initiate secondary IP warmup schedule with SendGrid (due 2025-04-25)

### Follow-ups

- Review deliverability metrics 30 days after DMARC enforcement goes live
- Revisit soft bounce retry strategy in next sprint based on ISP feedback loop data
