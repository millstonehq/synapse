---
id: PRD-010
type: prd
title: Adaptive MFA PRD
status: proposed
owner: Product Manager
created: '2025-12-02T15:31:14.958Z'
updated: '2026-09-29T12:53:57.080Z'
tags:
  - prd
  - user-authentication
summary: Adaptive MFA PRD
related_tdds:
  - TDD-007
  - TDD-009
example: true
related_standards:
  - STANDARD-009
---

## Summary

Adaptive MFA enhances the existing MFA system by applying risk-based authentication signals to decide when to prompt for an additional factor. Instead of always requiring MFA at login (high friction) or never requiring it after the first enrollment (low security), Adaptive MFA evaluates contextual risk signals and challenges users only when risk is elevated — for example, on new devices, unusual locations, or after a period of inactivity. This builds on the token lifecycle work in [[TDD-007|TDD-007: Token Refresh Service TDD]] and the passwordless infrastructure in [[TDD-009|TDD-009: Passwordless Login Flow TDD]].

## Goals

- Reduce MFA challenges for low-risk logins by 60%, improving user experience for trusted devices
- Increase the proportion of high-risk logins that receive an MFA challenge from 40% to 100%
- Reduce account takeover incidents by 40% compared to static MFA enforcement
- Achieve < 1% false positive rate (trusted users challenged unnecessarily)

## In Scope

- Risk signal collection: device fingerprint, IP geolocation, login time-of-day, user agent, failed login history
- Risk scoring model: deterministic rules engine (no ML initially) producing a risk score (low/medium/high)
- Adaptive MFA decision: skip MFA challenge for low-risk logins; require MFA for medium/high-risk
- Device trust: users can mark a device as trusted for 30 days after successful MFA; trusted devices receive reduced friction
- Admin controls: organization admins can set minimum MFA frequency (e.g., always require MFA regardless of risk) or disable adaptive behavior
- Risk event logging: all risk scores and MFA decisions logged for audit and model improvement

## Out of Scope

- Machine learning-based risk scoring (rules-based engine only in Phase 1)
- Continuous authentication (risk assessment during active sessions, not only at login)
- Third-party risk signal providers (e.g., threat intelligence feeds) in Phase 1
- Adaptive MFA for service accounts or API tokens

## Users and Flows

End users on trusted devices experience the primary benefit: they complete login without being prompted for MFA after their initial enrollment, as long as risk signals remain low. A user logging in from their usual laptop in their home city during business hours sees a fast login with no MFA prompt.

The same user logging in from an unrecognized device, or from an unusual country, receives an MFA challenge before their login completes. After successfully completing MFA, they can optionally mark the new device as trusted.

Administrators configure Adaptive MFA policy at the organization level. They can review the risk event log to understand why users were or were not challenged and adjust policy thresholds if false positives are too high.

## Requirements

- Risk signals must be collected on every login attempt without adding more than 20ms to login latency
- The risk scoring engine must produce a decision (skip/challenge) in under 5ms
- Device fingerprint must be stable across browser updates for at least 90 days without requiring re-enrollment
- Trusted device registration must use a signed, HttpOnly cookie with a 30-day TTL
- Device trust must be revocable by the user (in account settings) and by admins (in admin console)
- Risk event log must record: risk score, individual signal values, MFA decision, and outcome
- Adaptive MFA must not reduce security for users or organizations that have MFA always-on policy
- All risk signal collection must be disclosed in the privacy policy

## KPIs

- **MFA challenge reduction**: Target 60% reduction in challenges for low-risk logins
- **High-risk challenge rate**: Target 100% of high-risk logins receive MFA challenge
- **False positive rate**: Target < 1% of low-risk users challenged unnecessarily
- **Account takeover reduction**: Target 40% reduction in ATO among Adaptive MFA users vs. control group

## Information Architecture

- /settings/security/devices — view and manage trusted devices
- /admin/policies/mfa — adaptive MFA policy configuration (minimum MFA frequency, risk threshold)
- /admin/risk-events — risk event log viewer
- Technical design: [[TDD-007|TDD-007: Token Refresh Service TDD]], [[TDD-009|TDD-009: Passwordless Login Flow TDD]]

## Data Model

- **RiskScore**: login_attempt_id, user_id, device_fingerprint, ip_address, geo_country, geo_region, risk_score (low/medium/high), signal_breakdown, decision (skip/challenge), created_at
- **TrustedDevice**: device_id, user_id, fingerprint_hash, registered_at, expires_at, last_seen_at, name, trust_cookie_id

## Non-Functional

- Risk signal collection and scoring must add no more than 20ms to P99 login latency
- Device trust cookies must use SameSite=Strict and Secure flags
- Risk event logs must be retained for 12 months for security investigation purposes

## Constraints

- Adaptive MFA cannot reduce below the organization's configured minimum MFA frequency
- Device fingerprinting must not use browser APIs that require user permission (no canvas fingerprinting requiring consent)
- Risk scoring rules must be documentable and explainable for compliance purposes (no black-box ML in Phase 1)

## Risks

- **Risk**: Device fingerprint instability causes trusted users to be re-challenged frequently. Mitigation: Use multiple stable signals (user agent + OS + screen dimensions + timezone) and use fuzzy matching to tolerate minor changes.
- **Risk**: Attacker spoofs a trusted device fingerprint to bypass MFA. Mitigation: Combine fingerprint with a signed cookie; fingerprint alone is not sufficient for trust — the cookie is required.
- **Risk**: Adaptive MFA creates a false sense of security; low-risk logins that are not challenged could still be attackers. Mitigation: Clearly communicate that adaptive MFA reduces friction, not that it eliminates MFA entirely; high-sensitivity operations still require step-up MFA regardless of risk score.

## Milestones

### M1: Risk Signal Collection and Logging (Month 1-2)
#### Deliverables
- Device fingerprint generation and stable hashing
- IP geolocation lookup (using MaxMind GeoLite2)
- Risk event logging infrastructure
- Baseline data collection (no adaptive decisions yet — observe only)

#### Acceptance Criteria
- Risk signals collected on 100% of login attempts
- Risk event log queryable by user, date, and device
- < 20ms latency addition verified under load

### M2: Adaptive Decision Engine + Device Trust (Month 3-4)
#### Deliverables
- Rules-based risk scoring engine (low/medium/high)
- Adaptive MFA challenge skipping for low-risk logins
- Trusted device registration and management
- Admin policy controls (minimum MFA frequency, trust duration)

#### Acceptance Criteria
- 60% reduction in MFA challenges for returning users on known devices
- False positive rate < 1% in first 2 weeks (measured against manually labeled login sample)
- Trusted device revocation effective within 60 seconds
