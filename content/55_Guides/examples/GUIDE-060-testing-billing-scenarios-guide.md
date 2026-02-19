---
id: GUIDE-060
type: guide
title: Testing Billing Scenarios Guide
status: accepted
owner: Developer Experience
created: '2024-11-20T00:57:32.084Z'
updated: '2026-12-07T23:37:02.308Z'
tags:
  - guide
  - billing-engine
summary: Testing Billing Scenarios Guide
audience: internal
related_systems:
  - SYSTEM-049
  - SYSTEM-047
related_sops:
  - SOP-093
  - SOP-098
example: true
---

## Why Billing Testing Is Different

Billing bugs are unusually costly to fix after they reach production. An over-billing bug affects customer trust and requires manual credit issuance at scale. An under-billing bug causes revenue loss that may not be detected until the next finance review. Unlike most application bugs, billing errors often cannot be corrected with a simple code fix — they require data remediation, customer communication, and finance adjustments.

This is why the billing test suite is comprehensive and why integration testing against realistic billing scenarios is required before any billing change ships.

## Test Environment Setup

Use the staging billing environment for all pre-production billing testing. Staging mirrors production data models and integrations but uses Stripe test mode and does not send real emails. Test account IDs prefixed with `TEST-` are safe to operate on without affecting billing state for real customers.

For local development testing, use the local Docker Compose stack documented in the Billing Service Local Development Guide. The test harness in that environment allows time-travel (setting the "current date" to simulate billing cycle boundaries).

## Core Billing Scenarios to Test

Every billing-related change must be validated against these scenarios before merge:

**Scenario 1: Standard monthly invoice generation**
Create a test account on a flat subscription plan. Advance time to the next billing period boundary using the test harness time control. Verify a correctly formatted invoice is generated with the right amount, currency, and tax line items.

**Scenario 2: Usage-based billing with tier boundary**
Emit usage events crossing a tier boundary (e.g., 9,000 events at tier 1 rate and 3,000 at tier 2 rate). Run invoice generation and verify the line item breakdown reflects correct tier pricing.

**Scenario 3: Pro-ration on mid-cycle plan change**
Start an account on Plan A, advance to mid-month, change to Plan B. Verify the next invoice contains a pro-rated credit for unused Plan A days and a pro-rated charge for Plan B.

**Scenario 4: Subscription cancellation with pro-ration**
Create an active subscription. Submit a cancellation mid-cycle. Verify a pro-rated credit is issued for the unused billing period and no further invoices are generated after the cancellation effective date.

**Scenario 5: Credit application on invoice**
Issue a credit to a test account. Run invoice generation. Verify the credit is applied to the invoice total and the credit memo is linked on the invoice.

## Using the Billing Test Harness

The test harness CLI provides commands for all common test operations:

- `billing-test emit-usage --account TEST-ACCOUNT-002 --quantity 15000 --type api.request` — emit usage events
- `billing-test advance-time --days 30` — advance the billing clock
- `billing-test run-billing-cycle --account TEST-ACCOUNT-002` — trigger invoice generation for a specific account
- `billing-test assert-invoice --account TEST-ACCOUNT-002 --amount 5000 --currency USD` — assert the most recent invoice

## Next Steps

- Run the full billing scenario test suite before any change to billing calculation logic: `./gradlew :billing-scenarios:test`
- For changes affecting tax calculation, also run `./gradlew :billing-tax:integrationTest`
- Review postmortems for past billing incidents to understand what scenarios previously caused issues
