---
id: PRD-009
type: prd
title: SSO Self-Service Configuration PRD
status: accepted
owner: Product Manager
created: '2024-07-24T09:34:25.908Z'
updated: '2026-11-28T03:37:29.643Z'
tags:
  - prd
  - user-authentication
summary: SSO Self-Service Configuration PRD
related_tdds:
  - TDD-007
  - TDD-006
example: true
related_standards:
  - STANDARD-007
---

## Summary

SSO Self-Service Configuration enables enterprise organization administrators to configure, test, and manage their Single Sign-On integration without requiring a support ticket or engineering involvement. It leverages the Federated Identity Gateway from [[TDD-006|TDD-006: Federated Identity Gateway TDD]] and integrates with the token infrastructure from [[TDD-007|TDD-007: Token Refresh Service TDD]]. The goal is to reduce SSO setup time from an average of 1.3 admin-assisted days to under 1 hour of self-service work.

## Goals

- Reduce SSO setup time to under 1 hour for 80% of organizations
- Reduce SSO-related support tickets by 70%
- Increase SSO self-service adoption from 29% to 70% of new SSO setups
- Reduce SAML metadata upload error rate from 24% to under 5%

## In Scope

- SAML 2.0 SP-initiated SSO configuration (metadata upload or URL-based)
- OIDC provider configuration with guided setup for Okta, Azure AD, and Google Workspace
- Configuration validation with detailed error messages and guided resolution
- Test SSO connection before enabling for users
- Certificate management: view certificate expiry, upload replacement certificates
- 30-day advance certificate expiry notification (in-app and email)
- SSO enforcement policy: require SSO for all users or specific domains
- JIT (Just-In-Time) user provisioning configuration

## Out of Scope

- SCIM user provisioning (separate feature)
- IdP-initiated SAML (Phase 2)
- Multiple simultaneous SSO connections per organization
- Self-service for LDAP/AD (not supported in current platform)

## Users and Flows

IT administrators at enterprise organizations are the primary audience. They arrive at the SSO configuration page after being prompted by an onboarding guide or support documentation. The guided setup wizard walks them through: selecting their IdP (Okta, Azure AD, Google Workspace, or Custom), providing SP metadata to configure in their IdP, and then uploading/entering their IdP metadata.

For Okta and Azure AD (the most common providers), the wizard provides IdP-specific screenshots and step-by-step instructions for locating the metadata URL or XML. The SAML metadata upload step includes a pre-validation that checks for common issues (expired certificates, missing ACS URL, incorrect entity ID) before the user saves the configuration.

After initial configuration, a test button allows the admin to trigger a complete SSO login flow in a new browser tab and verify the result before enabling SSO for production users.

## Requirements

- SAML metadata can be configured via direct URL (auto-fetched and cached) or manual XML paste
- SAML metadata XML must be validated before saving: check signature algorithm, ACS URL, entity ID, and certificate expiry
- OIDC configuration must validate the discovery endpoint and confirm required scopes are available
- Test connection must simulate a full login flow end-to-end and report success or failure with diagnostic details
- Certificate expiry warnings must appear 30 days before expiry in the admin console and trigger email notification
- Certificate replacement must be possible without disabling SSO (upload new cert, set as active, remove old cert)
- JIT provisioning configuration must allow mapping of IdP groups to platform roles
- All configuration changes must be recorded in the admin activity log
- Configuration changes must take effect within 60 seconds for all new login attempts

## KPIs

- **Self-service setup completion rate**: Target 80% of admins complete SSO setup without opening a support ticket
- **SAML upload error rate**: Target < 5% of metadata uploads have validation errors (down from 24%)
- **Test connection success rate**: Target > 95% of test connections succeed after initial configuration
- **Setup time**: Target 80% of setups completed in under 1 hour
- **Support ticket reduction**: Target 70% fewer SSO setup/config support tickets

## Information Architecture

- /admin/sso — SSO configuration overview and status
- /admin/sso/setup — Guided setup wizard (IdP selection, SP metadata, IdP metadata, test, activate)
- /admin/sso/certificates — Certificate management (view, upload, manage expiry)
- /admin/sso/policy — SSO enforcement policy (required for all users, required for specific email domains)
- /admin/sso/provisioning — JIT provisioning and group-to-role mapping
- Technical design: [[TDD-006|TDD-006: Federated Identity Gateway TDD]]

## Data Model

- **SSOConnection**: org_id, protocol (saml/oidc), status (draft/active/disabled), config (idp_entity_id/issuer, metadata_url, certificates, acs_url, group_mappings)
- **SSOCertificate**: connection_id, certificate_pem, valid_from, valid_until, is_active, added_at, added_by
- **SSOTestResult**: connection_id, tested_at, outcome (success/failure), error_code, diagnostic_data

## Non-Functional

- Metadata URL fetch must complete within 10 seconds (timeout and show manual paste option)
- Configuration save must complete within 3 seconds
- Test connection flow must complete end-to-end within 30 seconds (includes IdP redirect and assertion processing)

## Constraints

- SSO setup requires the `org:admin` role
- SAML ACS URL must match a pre-configured allow-list for the platform's domains
- IdP certificates must use RSA-SHA256 or better; MD5 and SHA-1 certificates are rejected

## Risks

- **Risk**: SAML metadata validation is incomplete and allows misconfigured SSO that fails in production. Mitigation: Test the full login flow (not just config validation) as part of the activation step; do not allow SSO to be activated without a successful test.
- **Risk**: Admins upload a new certificate but forget to configure it in their IdP, breaking SSO. Mitigation: Certificate replacement wizard includes a "have you updated your IdP?" confirmation step; keep old certificate active until explicitly removed.

## Milestones

### M1: Core SAML Self-Service (Month 1-2)
#### Deliverables
- SAML metadata upload and URL-based configuration
- Pre-save metadata validation with detailed error messages
- Test connection flow
- Certificate management (view expiry, upload new)

#### Acceptance Criteria
- SAML metadata upload error rate < 5% (validated with internal beta)
- Test connection provides actionable diagnostic info for common errors
- Certificate expiry visible in admin console for all active SSO connections

### M2: OIDC Guided Setup + Enforcement Policy (Month 3)
#### Deliverables
- OIDC guided setup for Okta, Azure AD, Google Workspace
- SSO enforcement policy (all users or domain-specific)
- JIT provisioning with group-to-role mapping
- 30-day certificate expiry email notification

#### Acceptance Criteria
- OIDC setup completes in under 30 minutes for Okta/Azure AD with wizard
- SSO enforcement blocks non-SSO logins after policy activation
- JIT-provisioned users receive correct roles based on IdP group membership
