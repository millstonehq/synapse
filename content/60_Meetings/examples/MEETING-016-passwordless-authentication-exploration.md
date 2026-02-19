---
id: MEETING-016
type: meeting
title: Passwordless Authentication Exploration
status: approved
owner: Principal Engineer
created: '2024-03-19T12:35:37.974Z'
updated: '2025-08-25T00:29:17.067Z'
tags:
  - meeting
  - user-authentication
summary: Passwordless Authentication Exploration
company: UserAuthentication
topic: Passwordless Authentication Exploration
meeting_date: '2024-08-12T05:07:47.353Z'
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

- **Project**: Authentication Innovation
- **Topic**: Passwordless Authentication Exploration — Feasibility and Roadmap
- **Date/Time**: 2024-08-12 10:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Exploratory session to assess the feasibility of adding passwordless authentication (passkeys/WebAuthn and magic links) to the platform, driven by customer demand and industry momentum.

## Observations by Domain

- **WebAuthn/Passkeys**: Browser and OS support is now broad (Chrome, Safari, Firefox on desktop and mobile); the platform authenticator model (Face ID, Touch ID, Windows Hello) provides excellent UX; our auth service already has partial WebAuthn support for MFA that could be extended to primary authentication
- **Magic Links**: Simpler to implement than passkeys; already have email delivery infrastructure; security tradeoff is that email account compromise leads to platform compromise — less secure than passkeys for high-value accounts
- **Device Management**: Passkeys are device-bound (or synced via iCloud/Google Password Manager); users with multiple devices need a credential management UX; this is a significant frontend investment
- **Recovery Flows**: Passwordless increases the importance of account recovery; if a user loses their device and passkey, the fallback must be robust but not exploitable
- **Enterprise Considerations**: Enterprise customers using SAML SSO are unaffected; passkey addition is additive for direct-authentication users

## Key Metrics & Data Points

- **Current password-based login share**: 41% of logins (remaining 59% are SSO)
- **Password reset requests per month**: 1,200 (a significant support cost driver)
- **WebAuthn browser support coverage**: ~94% of our user browser/OS combinations
- **Estimated implementation effort (passkeys)**: 8–10 weeks for backend + frontend
- **Estimated implementation effort (magic links)**: 2–3 weeks

## Preliminary Scorecard Hooks

- Technical Feasibility: 4/5 - WebAuthn support largely in place; passkeys are an extension of existing work
- User Experience: 4/5 - Passkeys are excellent UX for supported devices; device management adds complexity
- Security Posture: 5/5 - Passkeys are phishing-resistant and stronger than passwords by design
- Implementation Effort: 3/5 - 8–10 weeks is significant; magic links are a faster quick win

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Account lockout from lost passkey device | High | Medium | Principal Engineer | Design robust fallback flow with secondary passkey enrollment required | 2024-09-01 |
| Magic link sent to compromised email creates chain breach | Medium | Low | Tech Lead | Magic links for high-value accounts require additional identity verification step | 2024-09-01 |
| Low adoption if device management UX is poor | Medium | Medium | Product Manager | Conduct usability testing with 10 users before broad rollout | 2024-10-01 |

## Decisions & Next Steps

### Decisions

- Magic links will be implemented first as a quick win to reduce password reset volume; 2–3 week timeline approved
- Passkeys (WebAuthn primary auth) will be planned for Q4 2024 as a larger initiative
- A backup passkey (second device enrollment) will be required at passkey setup to reduce account recovery risk

### Action Items

- Scope and schedule magic link implementation (Tech Lead — 2024-08-19)
- Design passkey device management UX and account recovery flow (Product Manager — 2024-09-15)
- Evaluate passkey sync providers (iCloud Keychain vs Google Password Manager) for cross-device support (Principal Engineer — 2024-09-01)

### Follow-ups

- Magic link implementation review at sprint end
- Passkey initiative kickoff scheduled for 2024-10-07
