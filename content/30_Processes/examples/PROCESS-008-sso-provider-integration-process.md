---
id: PROCESS-008
type: process
title: SSO Provider Integration Process
status: review
owner: Platform Lead
created: '2025-05-12T17:15:44.886Z'
updated: '2025-09-05T21:24:32.578Z'
tags:
  - process
  - user-authentication
summary: SSO Provider Integration Process
related_standards:
  - STANDARD-009
  - STANDARD-007
related_sops:
  - SOP-019
  - SOP-016
related_systems:
  - SYSTEM-010
example: true
---

## Purpose

This process ensures that new SSO (Single Sign-On) providers are evaluated, integrated, and validated in a consistent and secure manner before being made available to users. Uncontrolled SSO integrations introduce authentication bypass risks, token format inconsistencies, and audit gaps. This process governs the full lifecycle from vendor evaluation through production enablement.

## Scope

- New external identity providers (Google Workspace, Okta, Azure AD, etc.) being integrated as SSO sources
- Internal SAML or OIDC federation changes that modify existing SSO flows
- Changes to attribute mapping, group claim handling, or JIT (just-in-time) provisioning logic
- Updates to SSO provider metadata documents or signing certificates

## Roles and Responsibilities

- **Platform Lead**: Owns the integration process, approves the provider for production readiness, and ensures security review is completed
- **Security Engineer**: Reviews the provider's security posture, validates OIDC/SAML configuration, and approves cryptographic settings
- **Backend Engineer**: Implements the integration code, attribute mapping, and error handling per [[STANDARD-007|JWT Token Format Standard]]
- **QA Engineer**: Executes end-to-end authentication test cases including edge cases (account not found, MFA required, session expiry)

## Triggers

- A business request to support authentication via a new identity provider
- An existing SSO provider deprecating a supported feature or protocol version
- A security finding requiring migration away from a current SSO provider

## Inputs

- Provider's OIDC discovery document or SAML metadata XML
- Attribute mapping specification (email, user ID, group memberships)
- Security review approval from the Security Engineer

## Outputs

- Configured and tested SSO integration in the production authorization server
- Updated attribute mapping documentation
- Completed integration test report signed off by QA

## Steps

1. Submit an SSO integration request ticket including provider name, protocol (OIDC/SAML), and business justification
2. Security Engineer reviews the provider's security documentation and validates signing algorithms align with [[STANDARD-007|JWT Token Format Standard]]
3. Backend Engineer registers the application with the provider and obtains client credentials or metadata
4. Backend Engineer implements the integration in the staging environment including attribute mapping and error handling
5. QA Engineer executes the SSO integration test suite covering happy path, invalid credentials, MFA enforcement, and JIT provisioning
6. Platform Lead reviews the test report and approves promotion to production
7. Backend Engineer enables the integration in production via feature flag targeting an internal pilot group
8. Monitor authentication success rate and error logs for 48 hours before full rollout

## Controls

- All SSO integrations must use OIDC with PKCE or SAML 2.0; proprietary protocols are prohibited
- Provider signing certificates must be stored in the secrets manager, not in application configuration files
- SSO configuration changes in production require change ticket approval per organization change management policy
- Integration test coverage must include at least one negative test case for each failure mode
