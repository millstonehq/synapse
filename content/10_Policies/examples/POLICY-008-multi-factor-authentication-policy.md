---
id: POLICY-008
type: policy
title: Multi-Factor Authentication Policy
status: draft
owner: CISO
created: '2025-12-16T07:11:00.864Z'
updated: '2026-05-21T11:41:33.126Z'
tags:
  - policy
  - user-authentication
summary: Multi-Factor Authentication Policy
example: true
related_standards:
  - STANDARD-008
  - STANDARD-012
---

## Scope

This policy applies to all employees, contractors, and service accounts accessing internal systems, administrative interfaces, production infrastructure, and any system classified as sensitive or critical. It also applies to end-user authentication flows for any product feature that involves personal, financial, or privileged data access.

## Rationale

- Single-factor authentication based on passwords alone is insufficient against phishing, credential theft, and account takeover attacks
- MFA provides a second line of defense that significantly reduces unauthorized access even when passwords are compromised
- Industry data shows MFA prevents over 99% of automated credential attacks
- Compliance requirements under SOC 2, ISO 27001, and applicable data protection regulations mandate MFA for privileged access

## Policy Statements

- MFA is mandatory for all internal engineering systems, cloud console access, and CI/CD pipeline administration
- All privileged and administrative accounts must use hardware security keys (FIDO2/WebAuthn) or equivalent strong second factors
- TOTP-based authenticator apps are the minimum acceptable second factor for standard user accounts
- SMS-based OTP is permitted only as a fallback option and is prohibited as the sole second factor for privileged access
- Systems must not provide a mechanism to permanently bypass MFA except through an approved exception process reviewed by the CISO
- MFA enrollment completion rate must be tracked and reported monthly per [[STANDARD-012|Authentication Logging Standard]]
- Services must validate MFA challenges server-side; client-side bypass is prohibited

## Related Standards

- [[STANDARD-008|API Authentication Header Standard]]
- [[STANDARD-012|Authentication Logging Standard]]
