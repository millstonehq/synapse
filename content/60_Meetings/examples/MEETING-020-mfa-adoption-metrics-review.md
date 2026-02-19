---
id: MEETING-020
type: meeting
title: MFA Adoption Metrics Review
status: approved
owner: Principal Engineer
created: '2025-04-20T20:25:15.168Z'
updated: '2026-08-20T23:55:37.790Z'
tags:
  - meeting
  - user-authentication
summary: MFA Adoption Metrics Review
company: UserAuthentication
topic: MFA Adoption Metrics Review
meeting_date: '2025-02-12T11:40:39.869Z'
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

- **Project**: MFA Adoption Program
- **Topic**: MFA Adoption Metrics Review — 60 Days Post-Enforcement
- **Date/Time**: 2025-02-12 11:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Review of MFA adoption metrics 60 days after MFA enforcement was enabled for all users, assessing enrollment rates, support impact, and authentication success rates.

## Observations by Domain

- **Enrollment Rate**: 94% of active users are now enrolled in MFA (up from 82% at enforcement); 6% of accounts remain non-enrolled and are blocked from login
- **Factor Distribution**: TOTP authenticator apps represent 71% of MFA factors; WebAuthn (passkeys and hardware keys) represents 18%; SMS OTP represents 11%
- **Support Impact**: Account lockout and MFA support tickets peaked at 3x baseline in the first 2 weeks, then normalized to 1.2x baseline; net positive (fewer password reset tickets now that MFA is active)
- **Authentication Success Rate**: MFA challenge success rate is 97.8%; primary failure modes are expired TOTP codes (clock skew) and lost device scenarios
- **User Sentiment**: Post-enrollment survey (n=340) shows 78% positive or neutral; 22% negative (primarily "too many steps" feedback)

## Key Metrics & Data Points

- **MFA enrollment rate**: 94% of active users (6% blocked)
- **TOTP factor adoption**: 71% of enrolled users
- **WebAuthn factor adoption**: 18% of enrolled users
- **MFA challenge success rate**: 97.8%
- **Support ticket volume change**: +20% vs pre-enforcement baseline (down from +200% at peak)
- **Password reset tickets**: -45% vs pre-enforcement (significant reduction)

## Preliminary Scorecard Hooks

- Enrollment Progress: 4/5 - 94% is strong; remaining 6% are inactive or hard-to-reach accounts
- Authentication Experience: 4/5 - 97.8% success rate is good; TOTP clock skew issue needs addressing
- Support Impact: 4/5 - Net positive on support volume; initial spike was within managed range
- Factor Security Mix: 4/5 - TOTP dominant is acceptable; WebAuthn growth to 18% is healthy

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| 6% of blocked accounts belong to legitimate users who need support to enroll | Medium | High | Engineering Manager | Proactive outreach campaign to unenrolled accounts before next review | 2025-03-01 |
| TOTP clock skew causing 2.2% challenge failures | Medium | Medium | Tech Lead | Increase TOTP validation window; add in-app clock sync warning | 2025-02-25 |
| SMS OTP (11%) is weakest factor; users should migrate to TOTP | Low | Low | Product Manager | Add in-app nudge encouraging SMS users to add a TOTP authenticator | 2025-03-15 |

## Decisions & Next Steps

### Decisions

- MFA enforcement will remain in place; 94% enrollment and improving support metrics confirm the rollout was successful
- Unenrolled account outreach will be conducted by the customer success team; engineering will provide the account list
- TOTP clock skew fix (expanded validation window) will be implemented this sprint

### Action Items

- Implement expanded TOTP validation window (Tech Lead — 2025-02-25)
- Export list of 6% unenrolled accounts for customer success outreach (Principal Engineer — 2025-02-15)
- Design in-app nudge for SMS users to add TOTP (Product Manager — 2025-03-15)
- Publish MFA adoption metrics to the security dashboard (DevOps Lead — 2025-02-20)

### Follow-ups

- 90-day MFA adoption review scheduled for 2025-05-12
- WebAuthn passkey promotion campaign to be discussed in next product planning session
