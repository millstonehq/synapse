---
id: GUIDE-001
type: guide
title: Getting Started with Payment Integration
status: approved
owner: Developer Experience
created: '2024-09-20T03:21:03.289Z'
updated: '2025-03-12T06:28:28.406Z'
tags:
  - guide
  - payment-processing
summary: Getting Started with Payment Integration
audience: partner
related_systems:
  - SYSTEM-004
  - SYSTEM-005
related_sops:
  - SOP-009
  - SOP-004
example: true
---

## Why This Matters

Integrating with the payment platform allows you to accept payments from customers using cards, digital wallets, and bank transfers. A well-integrated payment flow increases checkout conversion, reduces fraud exposure, and ensures your transactions are processed in compliance with PCI DSS requirements.

This guide walks you through obtaining API credentials, making your first test charge, and handling the key response scenarios your integration must support before going live.

## Prerequisites

Before starting, ensure you have the following:

- A merchant account with an approved API application (contact your account manager if you do not have one)
- Your sandbox API key from the merchant portal (Settings > API Keys)
- A server-side environment capable of making HTTPS requests (all payment API calls must be made server-side; never expose API keys to browser or mobile clients)
- Basic familiarity with REST APIs and JSON

## Step-by-Step: Making Your First Payment

Your first integration goal is a successful test authorization and capture in the sandbox environment.

**Step 1: Create a payment intent.** Send a `POST /v1/payment-intents` request with the amount (in minor currency units), currency code, and an idempotency key. The response includes a `client_secret` that your frontend uses to collect payment method details.

**Step 2: Collect payment details.** Use the payment.js SDK on your checkout page to display the card collection form. The SDK handles PCI-compliant tokenization and returns a payment method token — your servers never see raw card data.

**Step 3: Confirm the payment.** Send a `POST /v1/payment-intents/{id}/confirm` with the payment method token. The platform submits the authorization to the gateway and returns the result.

**Step 4: Handle the response.** A `status: succeeded` response means the payment was authorized and captured. A `status: requires_action` means the customer must complete 3D Secure. A `status: failed` includes an `error_code` to show the customer an appropriate message.

## Common Questions

**Do I need to handle 3D Secure?** Yes. Your integration must handle `requires_action` responses and redirect customers to complete authentication. Failing to do so will result in declined transactions from issuers that mandate 3DS.

**What idempotency key should I use?** Use a unique key per payment intent creation attempt — typically a UUID tied to your internal order ID. Reusing the same key for a retry returns the original result without creating a duplicate charge.

**How do I test declined cards?** The sandbox provides test card numbers that simulate specific decline scenarios. Use `4000000000000002` for a generic decline and `4000000000009995` for an insufficient funds decline. See the sandbox testing guide for the full list.

## Next Steps

- Review the Payment Testing in Sandbox Mode guide before going live
- Implement webhook handling to receive asynchronous payment events
- Complete the integration checklist with your account manager before activating your production API key
