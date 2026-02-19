---
id: TDD-020
type: tdd
title: SMS Provider Abstraction Layer TDD
status: accepted
owner: Principal Engineer
created: '2024-11-14T14:56:20.266Z'
updated: '2025-09-09T22:04:23.858Z'
tags:
  - tdd
  - notification-service
summary: SMS Provider Abstraction Layer TDD
related_adrs:
  - ADR-0016
  - ADR-0017
example: true
---

## Summary

Design the SMS Provider Abstraction Layer — a Go package within the SMS Dispatch Service that encapsulates all provider-specific SMS integration logic behind a common interface, enabling transparent failover between Twilio (primary) and Vonage (secondary) without changes to the dispatch pipeline. The abstraction must support provider circuit breaking, per-provider delivery receipt processing, and startup health validation.

The layer implements the provider isolation pattern used for email in [[ADR-0016|ADR-0016: Use Firebase for Push Notifications]] and supports the template versioning reference model from [[ADR-0017|ADR-0017: Implement Template Versioning System]] for SMS template bodies.

## Overview

The SMS Provider Abstraction Layer is a Go package (`pkg/smsprovider`) that defines the `SmsProvider` interface and provides concrete implementations for Twilio and Vonage. The SMS Dispatch Service depends only on the interface, not on any provider-specific types, making the active provider fully swappable at configuration time or at runtime via circuit breaker.

Key design principles:
- **Interface-driven**: The `SmsProvider` interface is the only type the dispatch pipeline depends on. All provider-specific behavior is encapsulated in adapter structs.
- **Circuit breaker wrapping**: Provider adapters are wrapped with a circuit breaker that automatically activates the fallback provider after a configurable error threshold.
- **Startup validation**: The primary provider is health-checked at service startup. Startup fails if the primary provider is unreachable, preventing misconfiguration deployments (as occurred in POSTMORTEM-019).
- **Receipt processing**: Each provider delivers receipts via webhook. The abstraction includes a receipt normalizer that converts provider-specific webhook formats into a common `DeliveryReceipt` struct.

## Architecture

- **SmsProvider Interface**: Defines `Send(ctx, message) → SendResult` and `Name() → string`. All provider implementations satisfy this interface.
- **TwilioAdapter**: Implements `SmsProvider` using the Twilio REST API. Handles E.164 number formatting, Twilio error code mapping, and Messaging Service SID routing.
- **VonageAdapter**: Implements `SmsProvider` using the Vonage SMS API. Handles Vonage-specific `from` number selection and error code normalization.
- **CircuitBreakerProvider**: A decorator that wraps a primary and fallback `SmsProvider`. Tracks error counts in a sliding window; switches to fallback when the threshold is exceeded.
- **ReceiptNormalizer**: Converts Twilio and Vonage delivery receipt webhook payloads into a common `DeliveryReceipt` struct for Kafka publishing.
- **StartupValidator**: Called during service initialization. Sends a test message to the Twilio/Vonage sandbox to verify credentials and connectivity.

## Information Model

- **SmsMessage**: `messageId`, `to` (E.164), `body`, `from` (optional, provider selects if omitted), `priority`, `templateRef`, `idempotencyKey`
- **SendResult**: `messageId`, `providerMessageId`, `provider`, `status` (accepted|rejected|error), `errorCode` (if any), `sentAt`
- **DeliveryReceipt**: `messageId`, `providerMessageId`, `provider`, `status` (delivered|undelivered|failed), `errorCode`, `carrier`, `receivedAt`

## Interfaces

- `SmsProvider.Send(ctx context.Context, msg SmsMessage) → (SendResult, error)`
- `SmsProvider.Name() → string`
- `ReceiptNormalizer.NormalizeTwilio(payload TwilioReceiptPayload) → DeliveryReceipt`
- `ReceiptNormalizer.NormalizeVonage(payload VonageReceiptPayload) → DeliveryReceipt`
- `StartupValidator.Validate(ctx context.Context, provider SmsProvider) → error`

## Files and Layout

```
pkg/smsprovider/
  interface.go                  - SmsProvider interface definition
  twilio_adapter.go             - Twilio REST API implementation
  vonage_adapter.go             - Vonage SMS API implementation
  circuit_breaker_provider.go   - Circuit breaker decorator
  receipt_normalizer.go         - Webhook payload normalization
  startup_validator.go          - Startup health check
  types.go                      - SmsMessage, SendResult, DeliveryReceipt types
  errors.go                     - Provider error code constants and mapping
internal/
  dispatch/
    sms_dispatcher.go           - Dispatch pipeline; depends on SmsProvider interface only
```

## Work Plan

1. **Phase 1 - Interface and Types (Week 1)**: Define `SmsProvider` interface, all shared types, error constants
2. **Phase 2 - Twilio Adapter (Week 2)**: Twilio REST implementation, E.164 validation, error mapping, integration tests against Twilio sandbox
3. **Phase 3 - Vonage Adapter (Week 3)**: Vonage implementation, error mapping, integration tests against Vonage sandbox
4. **Phase 4 - Circuit Breaker (Week 4)**: Circuit breaker decorator, sliding window error tracking, failover and recovery logic
5. **Phase 5 - Receipts and Startup Validation (Week 5)**: Receipt normalizer for both providers, startup validator with test send capability

## Risks and Mitigations

- **Risk**: Provider API changes break adapters without notice. **Mitigation**: Pin SDK versions; run nightly integration tests against both provider sandboxes; subscribe to provider changelogs.
- **Risk**: Startup validator adds latency to service startup in CI/CD. **Mitigation**: Make startup validation configurable (enabled in production, disabled in test environments via `SMS_STARTUP_VALIDATION=false`).
- **Risk**: Circuit breaker switches to Vonage permanently if Twilio has an extended outage, and Vonage's lower rate limits cause queuing. **Mitigation**: Alert when circuit breaker has been open for > 15 minutes; operator can adjust Vonage rate limits or manually override provider selection.
