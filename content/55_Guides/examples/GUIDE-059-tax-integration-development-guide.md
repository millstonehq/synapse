---
id: GUIDE-059
type: guide
title: Tax Integration Development Guide
status: approved
owner: Engineering Team
created: '2024-10-13T17:09:41.687Z'
updated: '2026-02-23T09:27:17.342Z'
tags:
  - guide
  - billing-engine
summary: Tax Integration Development Guide
audience: internal
related_systems:
  - SYSTEM-046
  - SYSTEM-050
related_sops:
  - SOP-099
  - SOP-091
example: true
---

## Why Tax Integration Is Non-Trivial

Tax calculation in billing is not a lookup table problem — it is a multi-dimensional determination that depends on the customer's location, the product type, the transaction amount, and applicable exemptions. Getting it wrong means either over-billing customers (creating disputes and refunds) or under-collecting tax (creating regulatory liability for the company).

The Billing Engine provides a centralized Tax Calculation Service that handles this complexity. This guide explains how to integrate with it correctly and what to verify before your integration goes live.

## How the Tax Calculation Service Works

The Tax Calculation Service accepts a `TaxCalculationRequest` containing the taxable amount, customer billing address (or account tax jurisdiction override), and the product tax code. It returns itemized tax line items per jurisdiction along with the calculated amounts.

You never call the Tax Calculation Service directly from product code. The Billing Engine's invoice generation pipeline calls it automatically as part of generating invoice line items. If you are adding a new billable product, you only need to ensure the correct product tax code is set in the plan configuration.

The product tax code determines how the product is classified for tax purposes (SaaS software, professional services, tangible goods, etc.). An incorrect tax code is the most common cause of tax calculation errors on new product types.

## Configuring Product Tax Codes

When creating a new billing plan, the plan specification must include a `tax_code` for each billable line item type. Valid tax codes are defined in the tax code registry (accessible in the Billing Engine admin console under **Tax Configuration > Product Tax Codes**).

For SaaS products, the most common code is `SAAS_SUBSCRIPTION`. For usage-based API products, use `DIGITAL_SERVICE_USAGE`. If your product does not fit an existing code, work with Finance Operations to register a new one before plan activation.

## Testing Tax Calculation

Before enabling a new plan or product in production, validate tax calculation in the staging environment:

1. Create a test account with a billing address in each of your target markets (US, EU, UK are the most common).
2. Generate a test invoice via the billing test harness.
3. Verify the tax line items on the generated invoice: check that the correct jurisdiction is identified, the rate matches the current tax rate table, and the calculated amount is correct.
4. For EU accounts, verify that B2B accounts with a valid VAT number generate a zero-rated VAT line item (reverse charge).

## Handling Exemptions

Customers with tax-exempt status (non-profit organizations, resellers with resale certificates) can be configured with an exemption in the billing admin console. Exempt accounts will have a `tax_exempt: true` flag that causes the tax calculation service to return zero-rated tax line items.

Engineering should never hardcode exemption logic in product code. If you encounter a request to add special tax handling for specific accounts, direct it to Finance Operations to configure through the standard exemption process.

## Next Steps

- Review the Tax Calculation Standard for the complete specification
- Run the tax calculation integration test suite: `./gradlew :billing-tax:integrationTest`
- Consult Finance Operations before go-live for any product serving customers in new jurisdictions
