---
id: PROCESS-011
type: process
title: Security Token Rotation Process
status: approved
owner: Platform Lead
created: '2025-06-03T12:57:18.288Z'
updated: '2026-02-16T02:50:17.908Z'
tags:
  - process
  - user-authentication
summary: Security Token Rotation Process
related_standards:
  - STANDARD-008
  - STANDARD-011
related_sops:
  - SOP-014
  - SOP-012
related_systems:
  - SYSTEM-008
example: true
---

## Purpose

Security tokens and cryptographic signing keys have a finite safe lifetime. Rotating them on a defined schedule limits the blast radius of undetected key compromise and satisfies compliance requirements. This process defines how JWT signing keys, OAuth client secrets, and API keys are rotated without service disruption or user impact.

## Scope

- JWT signing keys (RSA and EC private keys) used by the authentication service
- OAuth client secrets for all registered OAuth applications
- Internal service API keys used for machine-to-machine authentication
- Encryption keys for session data at rest

## Roles and Responsibilities

- **Platform Lead**: Approves the rotation schedule and confirms completion of each rotation cycle
- **Security Engineer**: Generates new key material, updates secrets management, and validates compliance with [[STANDARD-008|API Authentication Header Standard]]
- **Deploying Engineer**: Updates service configuration to reference the new key material and executes rolling restarts
- **On-Call Engineer**: Monitors authentication health metrics during and after rotation

## Triggers

- Scheduled rotation interval reached (JWT signing keys: every 90 days; OAuth secrets: every 180 days)
- Suspected or confirmed key compromise reported via security alert
- Personnel with key access leaves the organization

## Inputs

- Current key inventory from the secrets manager showing key IDs, creation dates, and next rotation due dates
- Approved change ticket for the rotation operation
- New key material generated in the HSM or secrets manager

## Outputs

- All services updated to use the new key material with the old key decommissioned
- Updated key inventory with new rotation due dates
- Audit log entry confirming successful rotation per [[STANDARD-011|OAuth Scope Naming Standard]] compliance requirements

## Steps

1. Generate new key material in the secrets manager using the approved algorithm and key size
2. Add the new key to the authorization server's JWKS endpoint alongside the existing key (dual-key period)
3. Deploy updated authorization server configuration that signs new tokens with the new key while still accepting tokens signed by the old key
4. Monitor token validation error rates for 24 hours to confirm downstream services accept new tokens correctly
5. After token lifetime has elapsed (ensuring no valid tokens signed with the old key remain active), remove old key from the JWKS endpoint
6. Update all OAuth clients and service accounts to use the new credentials
7. Revoke the old key material from the secrets manager and confirm deletion
8. Update the key inventory and close the change ticket with rotation evidence

## Controls

- All key rotation must be performed in the secrets manager; plaintext key material must never appear in configuration files or source code
- Dual-key periods must last at least 1.5x the maximum token lifetime to prevent validation failures
- Key rotation must be tested in staging before production execution
- Rotation completion must be confirmed via automated JWKS endpoint validation, not manual inspection
