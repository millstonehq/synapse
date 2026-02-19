---
id: PRD-007
type: prd
title: Social Login Integration PRD
status: accepted
owner: Head of Product
created: '2024-03-11T09:46:40.720Z'
updated: '2026-09-30T15:12:52.358Z'
tags:
  - prd
  - user-authentication
summary: Social Login Integration PRD
related_tdds:
  - TDD-006
  - TDD-009
example: true
related_standards:
  - STANDARD-007
---

## Summary

Social Login Integration adds the ability for users to sign up and log in using their existing Google, GitHub, or Microsoft accounts. This reduces sign-up friction for developer-facing products (where GitHub accounts are ubiquitous) and consumer-facing products (where Google accounts are standard). It leverages the Federated Identity Gateway design from [[TDD-006|TDD-006: Federated Identity Gateway TDD]] and the passwordless login infrastructure from [[TDD-009|TDD-009: Passwordless Login Flow TDD]].

## Goals

- Reduce new user sign-up time from ~90 seconds (password-based) to under 15 seconds via social login
- Increase sign-up conversion rate by 20% within 3 months of launch
- Provide Google, GitHub, and Microsoft as initial providers at launch
- Maintain full account security posture (MFA requirement for enterprise, rate limiting, audit logging)

## In Scope

- "Sign in with Google" (OIDC)
- "Sign in with GitHub" (OAuth 2.0)
- "Sign in with Microsoft" (OIDC / Azure AD)
- Account linking: allow existing users to link a social provider to their account
- Account creation via social login for new users
- Profile data population from social provider claims (name, email, avatar)
- Social login available for both sign-up and sign-in flows
- Admin console toggle to disable specific social providers per organization

## Out of Scope

- Apple Sign-In (deferred to Phase 2)
- Facebook, Twitter/X, LinkedIn (low demand in user research)
- Social login for enterprise SSO (covered by Federated Identity Gateway)
- Automatic account merging when social email matches existing account without user consent

## Users and Flows

Individual users (free tier and small teams) are the primary audience for social login. They arrive at the sign-up or login page, click their preferred social provider, grant the minimal required permissions (name, email, avatar), and are redirected back to the platform with an authenticated session. For new users, an account is created automatically using the social provider's profile data; for existing users, the social identity is linked to their account on first use.

Enterprise users in organizations with SSO configured cannot use social login as a primary authentication method — their administrator's SSO policy takes precedence. Social login is available to enterprise users who are not governed by an SSO policy.

Developer users (accessing via API or CLI) are not affected by social login; social login applies to browser-based authentication only.

## Requirements

- Social login must use OIDC/OAuth 2.0 authorization code flow with PKCE for all providers
- The user's email from the social provider must be verified before account creation or linking
- Social login accounts must be subject to the same rate limiting as password-based accounts
- If a social provider returns an email that matches an existing account, the user must explicitly confirm account linking (no silent merge)
- All social login events must be recorded in the audit log with provider name, provider user ID, and timestamp
- Users must be able to unlink a social provider from account settings (provided another login method exists)
- Social login must coexist with MFA: users who have MFA enrolled complete MFA after social authentication
- Provider client credentials must be stored in HashiCorp Vault and rotated without service downtime

## KPIs

- **Social login adoption**: Target 30% of new sign-ups using social login within 3 months of launch
- **Sign-up conversion rate**: Target 20% improvement in sign-up completion rate
- **Social login success rate**: Target > 99% of initiated social login flows completed successfully
- **Account linking rate**: Target 15% of existing users linking a social account within 6 months

## Information Architecture

- Login/sign-up page: social login buttons below email/password form
- Account settings: /settings/connected-accounts — linked social accounts management
- Admin console: /admin/organizations/{id}/authentication — per-org social provider toggle
- Technical design: [[TDD-006|TDD-006: Federated Identity Gateway TDD]]

## Data Model

- **SocialIdentity**: provider (google/github/microsoft), provider_user_id, user_id (platform), email, name, avatar_url, linked_at, last_used_at
- **SocialLoginSession**: state parameter (PKCE state), provider, initiated_at, expiry, PKCE verifier

## Non-Functional

- Social login redirect round-trip (including provider auth) must complete in under 3 seconds P90
- Provider credential fetch (from Vault) must not block login; credentials must be cached in memory
- Social login must degrade gracefully if a provider is unavailable (show error message, not a 500)

## Constraints

- Provider OAuth apps must be registered with verified platform domain names (no localhost in production)
- Social login is browser-only; mobile apps use platform SDK OAuth flows (out of scope)
- GitHub does not always return a verified email in their token response; users without a public verified email must be prompted to add one

## Risks

- **Risk**: Provider outage prevents all social login for that provider. Mitigation: Graceful error message directing users to alternative login methods; monitor provider status pages.
- **Risk**: Social provider email scope returns unverified email, creating account linking confusion. Mitigation: Reject unverified emails from providers; GitHub users without a verified public email must add one before social login completes.
- **Risk**: Silent account merging (if email matches) creates unauthorized access if social account is compromised. Mitigation: Require explicit user confirmation for account linking in all cases.

## Milestones

### M1: Google Sign-In (Month 1)
#### Deliverables
- OIDC integration with Google, including profile data population
- Account linking flow with explicit confirmation
- Social login audit logging
- Connected accounts management in account settings

#### Acceptance Criteria
- Google sign-in available on login and sign-up pages
- New user sign-up via Google completes in under 15 seconds
- Account linking requires explicit user confirmation in 100% of cases

### M2: GitHub and Microsoft + Admin Controls (Month 2)
#### Deliverables
- GitHub OAuth 2.0 integration (with email verification handling)
- Microsoft OIDC integration
- Admin console toggle for per-org social provider control
- Provider credential rotation without downtime

#### Acceptance Criteria
- All 3 providers available and tested on major browsers
- Admin can disable specific providers per organization
- Social login success rate > 99% across all providers in first 2 weeks
