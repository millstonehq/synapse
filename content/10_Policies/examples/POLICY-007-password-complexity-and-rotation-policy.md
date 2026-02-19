---
id: POLICY-007
type: policy
title: Password Complexity and Rotation Policy
status: accepted
owner: CTO
created: '2024-04-13T13:36:16.804Z'
updated: '2025-05-11T13:53:32.118Z'
tags:
  - policy
  - user-authentication
summary: Password Complexity and Rotation Policy
example: true
related_standards:
  - STANDARD-007
  - STANDARD-010
---

## Scope

This policy applies to all user accounts, service accounts, and system accounts managed by the engineering organization. It covers passwords used for end-user authentication, administrative access, API keys, and shared service credentials. All systems that accept password-based authentication must enforce these requirements.

## Rationale

- Weak or reused passwords are consistently exploited in credential stuffing, brute force, and phishing attacks
- Password rotation limits the window of exposure when credentials are compromised without the organization's knowledge
- Complexity requirements reduce the effectiveness of dictionary and rainbow-table attacks
- Compliance frameworks including SOC 2 and NIST SP 800-63B require documented password policies

## Policy Statements

- User passwords must be a minimum of 12 characters and must include at least one uppercase letter, one lowercase letter, one digit, and one special character
- Passwords must not contain the account username, email address, or common dictionary words
- Privileged and service account passwords must be a minimum of 20 characters and must be rotated every 90 days
- End-user passwords must be rotated at least annually and immediately upon suspected compromise
- Password reuse of the last 12 passwords is prohibited; systems must enforce this through hashed history
- Systems must enforce account lockout after 5 consecutive failed login attempts within a 10-minute window
- Temporary passwords issued during account setup or password reset must expire within 24 hours and require change on first use

## Related Standards

- [[STANDARD-007|JWT Token Format Standard]]
- [[STANDARD-010|Session Cookie Standard]]
