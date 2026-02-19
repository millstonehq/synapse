---
id: MEETING-040
type: meeting
title: Multi-Channel Notification Strategy Sync
status: approved
owner: Principal Engineer
created: '2025-10-10T19:21:09.059Z'
updated: '2026-10-10T14:02:40.910Z'
tags:
  - meeting
  - notification-service
summary: Multi-Channel Notification Strategy Sync
company: NotificationService
topic: Multi-Channel Notification Strategy Sync
meeting_date: '2026-11-14T20:15:56.740Z'
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

- **Project**: Notification Service - Multi-Channel Strategy
- **Topic**: Multi-Channel Notification Strategy Sync
- **Date/Time**: 2026-11-14 20:15 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: As the platform expands to new markets and channels, the team needs to align on the multi-channel notification strategy: how channel selection, fallback, and user preference management will work at scale.

## Observations by Domain

- **Channel Selection Logic**: Currently callers specify a channel explicitly; there is no intelligent channel selection based on user history, engagement, or context (e.g., prefer push if user hasn't opened email in 30 days)
- **Fallback Chains**: Fallback from failed push to email exists but is inconsistently configured; no standard fallback policy across all notification types
- **Preference Granularity**: Users can opt out of channels globally but not per-notification-type per-channel; product wants a matrix-style preference model
- **WhatsApp Interest**: Product team is evaluating WhatsApp Business API for markets where SMS deliverability is poor; requires significant integration work and a new vendor contract
- **International Compliance**: Adding markets (EU, APAC) requires channel-specific compliance rules (e.g., GDPR consent for email marketing in EU, different SMS opt-in rules in APAC)

## Key Metrics & Data Points

- **Users with email-only preference (no push)**: 31%
- **Users who have not opened email in 30 days but have active push tokens**: 18%
- **Markets with poor SMS deliverability (< 80%)**: 3 (targeting expansion regions)
- **WhatsApp adoption in target markets**: 65-80% for key APAC markets
- **Compliance rules requiring custom handling**: 2 new markets identified for Q1

## Preliminary Scorecard Hooks

- Channel Selection Intelligence: 2/5 - Static, caller-specified, no engagement signals
- Fallback Coverage: 2/5 - Inconsistent across notification types, no standard policy
- Preference Model Flexibility: 2/5 - Channel-level only, no per-type per-channel matrix
- Channel Expansion Readiness: 3/5 - Abstract interface makes new channels feasible, compliance gaps exist
- International Compliance Readiness: 2/5 - GDPR handled for existing channels, APAC rules not yet mapped

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| WhatsApp integration underestimated; delays Q1 expansion | High | Medium | Principal Engineer | Spike to size integration before committing to Q1 | 2026-12-01 |
| Preference matrix complexity overwhelms users in UI | Medium | Medium | Product Manager | Design progressive disclosure: show simple view by default | 2026-12-15 |
| APAC SMS compliance rules not understood before launch | High | Medium | Tech Lead | Engage legal for APAC market compliance review before channel activation | 2026-11-28 |

## Decisions & Next Steps

### Decisions

- A standardized fallback chain configuration will be introduced and required for all new notification types
- WhatsApp integration will be scoped as a Q1 spike before any commitment to delivery
- The preference model will be extended to per-type per-channel in Q1; a simplified UI hides complexity from users

### Action Items

- Tech Lead to define standard fallback chain configuration schema (due 2026-11-28)
- Principal Engineer to run WhatsApp integration spike and estimate (due 2026-12-01)
- Product Manager to coordinate legal review of APAC SMS compliance requirements (due 2026-11-28)

### Follow-ups

- WhatsApp spike results to be shared with the team before Q1 planning deadline
- Preference model UX designs to be reviewed before engineering kickoff
