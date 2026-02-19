---
id: TDD-043
type: tdd
title: Customer Settings API TDD
status: approved
owner: Tech Lead
created: '2024-06-26T06:46:24.929Z'
updated: '2025-09-21T11:13:44.562Z'
tags:
  - tdd
  - customer-portal
summary: Customer Settings API TDD
related_adrs:
  - ADR-0035
  - ADR-0036
example: true
---

## Summary

Design the Customer Settings API that backs the portal's Settings page: a unified endpoint for reading and writing customer preferences, communication opt-ins, security settings (password change, MFA enrollment), and notification preferences. This TDD covers the GraphQL schema extensions in the Customer API Gateway as specified in [[ADR-0035|ADR-0035]] and the federated module boundary agreed in [[ADR-0036|ADR-0036]].

## Overview

The Settings page is owned by the Core Portal team's federated remote. All settings mutations flow through the Customer API Gateway to the Customer Preference Service, which owns the canonical settings store. The Settings API adds a dedicated `customerSettings` top-level query and a set of typed mutation fields that replace ad-hoc REST calls made by the legacy settings page.

Key design principles:
- **Typed preference groups**: Settings are grouped into `ProfileSettings`, `NotificationSettings`, `SecuritySettings`, and `CommunicationSettings`; each group is its own GraphQL type to enable partial fetches
- **Optimistic UI**: Mutation responses include the updated settings object so the UI can apply optimistic updates without a refetch
- **Validation at the gateway**: Input validation (email format, password strength) runs in the gateway resolver, not in the Preference Service, to provide fast feedback before the downstream call
- **Audit trail**: Every settings mutation publishes a `settings.changed` event to the portal event bus; the event includes actor, changed fields, and old values

## Architecture

- **CustomerSettings resolver** (Customer API Gateway): Aggregates data from Preference Service (notification/communication settings) and the Identity Service (profile, security settings) in a single `customerSettings` query
- **Settings mutations**: Individual mutation resolvers delegate to the appropriate downstream service; errors from the downstream are surfaced as typed `UserError` objects in the GraphQL response
- **Settings Remote** (Module Federation): The Settings page exposes a `SettingsApp` federated module; the host shell mounts it at `/settings`

## Information Model

- **CustomerSettings**: `{ profile: ProfileSettings, notifications: NotificationSettings, communication: CommunicationSettings, security: SecuritySettings }`
- **ProfileSettings**: `{ displayName: String, email: String, language: LanguageCode, timezone: String }`
- **NotificationSettings**: `{ emailDigestEnabled: Boolean, inAppEnabled: Boolean, mutedCategories: [NotificationCategory] }`
- **CommunicationSettings**: `{ marketingEmailEnabled: Boolean, productUpdateEmailEnabled: Boolean, smsEnabled: Boolean }`
- **SecuritySettings**: `{ mfaEnabled: Boolean, mfaMethod: MfaMethod, lastPasswordChange: DateTime }`

## Interfaces

- `query CustomerSettingsPage { customerSettings { profile { displayName email } notifications { emailDigestEnabled inAppEnabled } communication { marketingEmailEnabled } security { mfaEnabled } } }` — full settings page query
- `mutation UpdateProfileSettings(input: UpdateProfileInput!)` — update display name, email, language, timezone
- `mutation UpdateNotificationSettings(input: UpdateNotificationInput!)` — update notification preferences
- `mutation UpdateCommunicationSettings(input: UpdateCommunicationInput!)` — update marketing/product email opt-ins
- `mutation EnrollMfa(method: MfaMethod!)` — initiate MFA enrollment flow; returns challenge object
- `mutation ChangePassword(currentPassword: String!, newPassword: String!)` — change portal password

## Files and Layout

```
app/
  settings/
    page.tsx                    - Server component: loads initial settings via GraphQL
    loading.tsx                 - Skeleton layout for settings page
components/
  settings/
    ProfileSettingsForm.tsx     - Client component: profile form with optimistic update
    NotificationSettingsForm.tsx- Client component: notification toggles
    CommunicationSettingsForm.tsx- Client component: communication opt-ins
    SecuritySettingsPanel.tsx   - Client component: MFA enrollment, password change
lib/
  graphql/
    settings.graphql            - Query and mutation definitions
    generated/                  - Generated TypeScript types
```

## Work Plan

1. **Phase 1 - Schema design (Week 1)**: Define `CustomerSettings` type hierarchy in GraphQL schema; agree on mutation input types with Preference Service and Identity Service teams
2. **Phase 2 - Resolvers (Week 2)**: Implement `customerSettings` query resolver aggregating Preference Service and Identity Service; implement `UpdateProfileSettings` and `UpdateNotificationSettings` mutations
3. **Phase 3 - Security mutations (Week 3)**: Implement `ChangePassword` and `EnrollMfa` mutations with appropriate validation and error types; end-to-end test with Identity Service
4. **Phase 4 - Frontend (Week 4)**: Build form components with optimistic UI for all four settings groups; wire to mutations
5. **Phase 5 - Testing and audit (Week 5)**: Unit tests for all resolvers; E2E tests for settings save flows; verify `settings.changed` events are published for each mutation

## Risks and Mitigations

- **Risk**: Settings page aggregates data from two downstream services; one being slow delays the whole page. **Mitigation**: Use `Promise.all` for parallel resolver fetches; apply a 3-second timeout with graceful empty-state fallback per settings group.
- **Risk**: Breaking changes to the `CustomerSettings` type affect the Settings Remote federated module. **Mitigation**: Treat all `CustomerSettings` fields as non-breaking additions only; removals require a deprecation period and cross-team sign-off per [[ADR-0036|ADR-0036]].
- **Risk**: Password change mutation could be brute-forced if rate limiting is not enforced. **Mitigation**: Apply per-customer rate limiting at the gateway for the `ChangePassword` mutation (3 attempts per 15 minutes).
