---
id: PROCESS-056
type: process
title: Billing Plan Configuration Process
status: approved
owner: Director of Engineering
created: '2024-08-13T02:15:51.218Z'
updated: '2025-03-01T21:20:54.485Z'
tags:
  - process
  - billing-engine
summary: Billing Plan Configuration Process
related_standards:
  - STANDARD-058
  - STANDARD-055
related_sops:
  - SOP-099
  - SOP-100
related_systems:
  - SYSTEM-049
example: true
---

## Purpose

The Billing Plan Configuration Process governs how new billing plans, pricing tiers, and plan modifications are created, reviewed, and activated in the Billing Engine. Billing plan configurations directly affect customer charges and revenue calculations, so they require structured review and controlled activation to prevent billing errors.

This process applies to all plan-related changes including new plan creation, price adjustments, feature entitlement changes, and plan deprecations.

## Scope

- Creation and modification of subscription billing plans and usage-based pricing tiers
- Assignment of plans to customer accounts and account segments
- Deprecation and retirement of existing billing plans
- Configuration of promotional pricing, discounts, and trial periods

## Roles and Responsibilities

- **Product Manager**: Authors the plan specification and business requirements; owns the plan definition before it enters the configuration workflow
- **Billing Platform Engineer**: Implements the plan configuration in the Billing Engine, validates pricing logic, and runs test billing simulations
- **Finance Operations**: Reviews the financial impact of new plans or price changes and confirms revenue projection accuracy
- **Director of Engineering**: Approves activation of plans that affect more than 10% of active accounts or involve pricing changes greater than 15%

## Triggers

- Product Manager submits a plan change request through the billing configuration ticket system
- Scheduled pricing review cycle (quarterly) that may result in rate card updates

## Inputs

- Plan specification document from Product (includes name, pricing model, tier definitions, entitlements, and effective date)
- Revenue impact assessment prepared by Finance Operations
- Approval from Director of Engineering for significant pricing changes

## Outputs

- Configured and validated billing plan record in the Billing Engine
- Plan activation confirmation with effective date
- Updated pricing documentation published to customer-facing documentation

## Steps

1. Product Manager creates a plan change ticket with the full plan specification and requested effective date
2. Billing Platform Engineer reviews the specification for completeness and feasibility within the Billing Engine data model
3. Engineer implements the plan configuration in the staging environment and runs billing simulation tests against representative accounts
4. Finance Operations reviews the simulation output to validate pricing calculations and projected revenue impact
5. Director of Engineering approves activation if the plan meets the significance thresholds defined in the Scope section
6. Engineer schedules the plan activation for the specified effective date, creating a scheduled activation record
7. On the effective date, the plan activates automatically; Engineer monitors billing metrics for any anomalies during the first 24 hours

## Controls

- No billing plan may be activated in production without a validated staging simulation on file
- Plan changes with a retroactive effective date are prohibited without written approval from the Director of Engineering
- All plan configuration changes are versioned and the prior configuration must be restorable within 1 hour if needed
