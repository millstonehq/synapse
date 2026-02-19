---
id: MEETING-013
type: meeting
title: Auth Service Performance Review
status: draft
owner: Product Manager
created: '2025-12-22T18:20:57.020Z'
updated: '2026-08-14T08:16:51.700Z'
tags:
  - meeting
  - user-authentication
summary: Auth Service Performance Review
company: UserAuthentication
topic: Auth Service Performance Review
meeting_date: '2024-06-22T03:29:08.956Z'
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

- **Project**: Auth Service Platform
- **Topic**: Auth Service Performance Review — Q2 2024
- **Date/Time**: 2024-06-22 11:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Quarterly performance review of the authentication service triggered by a reported increase in P95 login latency over the past 30 days.

## Observations by Domain

- **Login Latency**: P95 login latency has increased from 95ms to 310ms over 30 days; the regression correlates with a 40% increase in active user count, suggesting the auth database is the bottleneck
- **Token Validation**: Token validation latency is unchanged at P50 8ms / P95 22ms; JWKS caching is effective
- **Database Performance**: Auth database shows increasing query times for session lookup; the `sessions.user_id` index is fragmented and has not been vacuumed recently
- **Autoscaling**: Auth service pods are autoscaling correctly; the bottleneck is the database, not the application tier
- **Session Cleanup**: Expired session records have accumulated to 1.2M rows; cleanup job is running but not keeping up with current growth rate

## Key Metrics & Data Points

- **Login P50 latency**: 145ms (up from 62ms 30 days ago)
- **Login P95 latency**: 310ms (up from 95ms 30 days ago; SLO target: 500ms)
- **Active sessions in DB**: 2.8M (1.2M expired and not yet cleaned)
- **Auth DB CPU utilization**: 68% (high; threshold for concern is 70%)
- **Session cleanup job throughput**: 50,000 records/hour (insufficient at current growth rate)

## Preliminary Scorecard Hooks

- Latency Performance: 3/5 - Still within SLO but trend is concerning; database is the bottleneck
- Database Health: 2/5 - Index fragmentation, accumulated expired sessions, near-threshold CPU
- Scalability: 4/5 - App tier scales well; database scaling strategy needed
- Observability: 4/5 - Metrics are good; database query profiling visibility could be improved

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Auth DB CPU reaches 100% causing login failures | High | Medium | Tech Lead | Run VACUUM ANALYZE on sessions table immediately; increase cleanup job throughput | 2024-06-25 |
| P95 latency breaches 500ms SLO within 2 weeks | High | Medium | Principal Engineer | Add read replica for session lookups to reduce primary DB load | 2024-07-10 |
| Session cleanup job falls further behind | Medium | High | DevOps Lead | Increase cleanup job batch size and run frequency | 2024-06-24 |

## Decisions & Next Steps

### Decisions

- Emergency maintenance window to VACUUM ANALYZE the sessions table is approved for this week
- Read replica for session lookups is approved as a Q3 infrastructure investment
- Session cleanup job will be tuned immediately as a low-risk quick win

### Action Items

- Schedule maintenance window for VACUUM ANALYZE on sessions table (Tech Lead — 2024-06-25)
- Tune session cleanup job batch size from 1,000 to 10,000 records (DevOps Lead — 2024-06-24)
- Create infrastructure ticket for auth database read replica (Principal Engineer — 2024-07-01)
- Set up P95 latency alert at 400ms to give earlier warning before SLO breach (DevOps Lead — 2024-06-25)

### Follow-ups

- Follow-up performance review in 3 weeks to confirm latency trend has reversed
- Auth database capacity planning to be included in Q3 planning sessions
