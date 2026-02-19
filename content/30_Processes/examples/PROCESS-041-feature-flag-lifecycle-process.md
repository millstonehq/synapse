---
id: PROCESS-041
type: process
title: Feature Flag Lifecycle Process
status: proposed
owner: Platform Lead
created: '2024-05-14T23:34:45.087Z'
updated: '2025-10-16T13:55:26.421Z'
tags:
  - process
  - ci-cd-platform
summary: Feature Flag Lifecycle Process
related_standards:
  - STANDARD-037
  - STANDARD-042
related_sops:
  - SOP-069
  - SOP-064
related_systems:
  - SYSTEM-034
example: true
---

## Purpose

This process manages feature flags from creation through retirement, ensuring that flags are used intentionally, tracked consistently, and cleaned up promptly after they serve their purpose. Feature flags enable safe deployment of incomplete or experimental features, but unconstrained flag proliferation leads to configuration debt, untested code paths, and operational complexity. This process provides guardrails to capture the benefits of feature flags while controlling the associated risks.

## Scope

- All feature flags controlling production behavior in any service
- Flags used for A/B testing, gradual rollouts, kill switches, and operational toggles
- Does not apply to environment-specific configuration values that are not intended to change dynamically

## Roles and Responsibilities

- **Feature Owner**: Requests flag creation, defines rollout criteria, monitors flag performance, and initiates retirement
- **Platform Engineer**: Creates the flag in the feature flag service, configures targeting rules, and validates flag plumbing in the pipeline
- **QA Engineer**: Verifies that the feature behaves correctly in all flag states (on/off/partial) before production rollout
- **Release Manager**: Approves flag activation in production and ensures the flag is registered in the deployment record

## Triggers

- An engineer requests a new feature flag for a feature under development
- A feature flag reaches 100% rollout and is ready for retirement
- A flag has been inactive for more than 90 days and requires review

## Inputs

- Feature flag request form: flag name, owning service, flag type (release/experiment/ops), default state, rollout plan, and expected retirement date
- QA sign-off confirming the feature is tested in all flag states
- Approval from the release manager for production activation

## Outputs

- Feature flag created in the flag management system with owner and retirement date recorded
- Flag activated in production according to the approved rollout plan
- Retired flag removed from code and flag management system, with removal verified by CI
- Flag lifecycle record retained for audit purposes

## Steps

1. Feature Owner submits a feature flag request, specifying the flag name (must follow naming convention `<service>.<feature>.<type>`), type, default state, and expected retirement date
2. Platform Engineer creates the flag in the feature flag service and validates the SDK integration in the development environment
3. QA Engineer tests the feature in all flag states and signs off on the test report
4. Release Manager approves production activation and adds the flag to the deployment record for the associated release
5. Feature Owner activates the flag at the approved rollout percentage (typically starting at 1%, then 10%, 50%, 100%) and monitors metrics at each increment
6. Upon reaching 100% rollout with stable metrics, Feature Owner initiates flag retirement by opening a cleanup PR that removes all flag evaluation code
7. Platform Engineer validates that CI passes with the flag code removed and that no evaluation calls remain
8. Feature Owner closes the flag in the flag management system and updates the retirement record

## Controls

- Feature flags may not remain at a partial rollout percentage for more than 30 days without a documented reason; flags stalled in rollout are flagged in the weekly platform review
- Flags must not be created without a recorded expected retirement date; flags without retirement dates are rejected
- The total number of active feature flags per service must not exceed 20; requests that would exceed this limit require platform lead approval
