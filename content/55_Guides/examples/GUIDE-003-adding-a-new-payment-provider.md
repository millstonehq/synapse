---
id: GUIDE-003
type: guide
title: Adding a New Payment Provider
status: review
owner: Engineering Team
created: '2024-03-13T12:17:09.339Z'
updated: '2026-10-04T19:04:12.334Z'
tags:
  - guide
  - payment-processing
summary: Adding a New Payment Provider
audience: internal
related_systems:
  - SYSTEM-001
  - SYSTEM-002
related_sops:
  - SOP-006
  - SOP-010
example: true
---

## Why Add a New Provider

The payment platform uses an abstracted provider adapter pattern so that new payment gateways, acquiring banks, or alternative payment method processors can be integrated without changes to the core payment service. Common reasons to add a new provider include expanding to a new geographic market, reducing gateway fees through provider diversification, adding support for a new payment method that requires a specialized processor, or providing redundancy through a secondary gateway.

## Architecture Overview

Each payment provider is implemented as a provider adapter that implements the `PaymentProviderAdapter` interface. The adapter is responsible for translating the platform's internal payment request model into the provider's API format, handling authentication, and translating provider responses back to the platform's standard response model including error code normalization.

The adapter is registered in the provider registry with a provider key (e.g., `stripe`, `adyen`, `braintree`) and a configuration schema. The payment routing engine selects the provider based on routing rules configured per merchant, payment method, and geography.

## Step-by-Step: Implementing a New Adapter

1. **Create the adapter class** in `packages/payment-service/src/providers/{provider-name}/`. Implement all methods of `PaymentProviderAdapter`: `authorize`, `capture`, `void`, `refund`, and `healthCheck`.
2. **Implement authentication** using the provider's preferred mechanism (OAuth, HMAC, API key header). Store credentials references only — the adapter reads values from the secrets manager at runtime.
3. **Normalize error codes** — map all provider-specific error codes to the platform's standard error code enum. This is critical for retry logic and merchant-facing error messages.
4. **Write unit tests** covering success, decline, timeout, and idempotent retry scenarios using mocked HTTP responses from the provider's API.
5. **Register the adapter** in `packages/payment-service/src/providers/registry.ts` with the provider key and configuration schema.
6. **Add sandbox credentials** to the sandbox secrets manager path and update the provider integration test suite.
7. **Run the full integration test matrix** against the provider's sandbox environment.
8. **Submit a PR** with the implementation, tests, and a completed provider adapter checklist.

## Configuration and Credentials

Provider credentials must be stored in the secrets manager under the path `payment-service/providers/{provider-name}/{environment}`. The adapter reads credentials at startup and caches them with a TTL of 5 minutes to support key rotation without restarts.

Never hardcode credentials, commit test credentials to source control, or log credential values. The CI pipeline includes a secrets scan that blocks merges containing credential patterns.

## Next Steps

- After the PR is merged, follow the Payment Provider Onboarding Process to complete security review and compliance sign-off
- Add the provider to the routing configuration in the payment routing service
- Update the payment observability dashboard to include per-provider metrics for the new adapter
