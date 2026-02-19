---
id: SOP-014
type: sop
title: Onboard New SSO Provider SOP
status: approved
owner: Release Manager
created: '2025-09-20T21:22:21.875Z'
updated: '2026-09-20T17:20:36.970Z'
tags:
  - sop
  - user-authentication
summary: Onboard New SSO Provider SOP
related_process: PROCESS-012
related_systems:
  - SYSTEM-008
example: true
---

## Preconditions

- The SSO provider has been approved via the SSO Provider Integration Process (PROCESS-012)
- Security review of the provider has been completed and signed off
- The provider's OIDC discovery document or SAML metadata is available
- An approved change ticket exists for this onboarding
- A staging environment has been configured and tested with the new provider

## Materials/Access

- Access to the authorization server administration console or configuration repository
- OAuth client ID and secret (or SAML certificate) from the new provider
- Access to the secrets manager to store the provider credentials
- The provider's OIDC discovery URL or SAML metadata XML
- Attribute mapping specification document approved by the Platform Lead

## Procedure

1. Store the provider's client secret or SAML certificate in the secrets manager under the path `sso-providers/<provider-name>/credentials`; never store in plaintext configuration files.
2. Add the provider's OIDC discovery URL or SAML metadata to the authorization server configuration in the feature-flagged `sso_providers` configuration block.
3. Configure the attribute mapping: map the provider's user identifier claim to the internal `sub` field, email claim to `email`, and group claims to internal role identifiers.
4. Deploy the updated authorization server configuration to the staging environment and run the SSO integration test suite.
5. Verify end-to-end login flow in staging: initiate login, complete provider authentication, confirm redirect back to the application with a valid JWT.
6. Enable the provider in production via feature flag targeting a pilot group of 10–20 internal users.
7. Monitor the pilot group's authentication success rate and error logs for 24 hours.
8. If pilot is successful, expand to full availability by updating the feature flag rollout to 100% and publishing the SSO option in the login UI.
9. Update the provider registry documentation with the new provider's details and close the change ticket.

## Validation

- Login via the new SSO provider completes successfully and issues a valid JWT
- JWT claims include all required fields and the user is assigned the correct roles based on provider group claims
- No authentication errors appear in logs for the pilot user group during the 24-hour monitoring window
- The provider appears correctly in the authorization server's discovery endpoint

## Rollback

1. If the SSO provider configuration causes authentication errors, disable the provider via feature flag immediately; existing users are unaffected as they fall back to other available authentication methods.
2. If attribute mapping errors result in incorrect role assignment, disable the provider, correct the mapping configuration, and re-run the staging test suite before re-enabling.
3. If the provider's credentials are compromised, revoke them in the secrets manager, generate new credentials from the provider, and re-deploy the updated configuration.
4. Document all rollback actions and root cause findings in the change ticket.
