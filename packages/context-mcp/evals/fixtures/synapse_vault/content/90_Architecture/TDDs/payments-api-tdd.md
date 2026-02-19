---
id: payments-api-tdd
type: tdd
title: Payments API — Technical Design
status: approved
owner: Principal Engineer
created: "2025-06-15T00:00:00.000Z"
updated: "2026-02-19T00:00:00.000Z"
tags:
  - tdd
  - payments
  - stripe
  - paypal
  - api
summary: Technical design for the Payments API service supporting Stripe and PayPal.
related_adrs: []
---

## Summary

This document describes the technical design of the Payments API. The service processes credit card payments through multiple payment providers (Stripe and PayPal), handles refunds, and provides payment history for authenticated users.

## Architecture

The Payments API is a REST service built with Express.js and TypeScript. It uses the Stripe Node.js SDK and PayPal client for payment processing across multiple providers.

### Components

- **Routes** (`src/routes/payments.ts`): Express router with three endpoints: `/charge`, `/refund`, `/history`
- **PaymentService** (`src/services/payment.ts`): Business logic layer handling multi-provider payment processing
- **Config** (`src/config/index.ts`): Environment-based configuration for payment provider keys and database

### Data Flow

1. Client sends payment request to `/payments/charge` with provider field
2. Auth middleware validates JWT token
3. PaymentService dispatches to appropriate provider (Stripe or PayPal)
4. Selected provider processes the charge and returns result
5. Response sent back to client with provider information

## API Endpoints

### POST /payments/charge

Process a payment charge via the selected provider.

**Request Body:**
- `amount` (number, required): Amount in cents
- `currency` (string, required): ISO 4217 currency code
- `provider` (string, required): Payment provider ('stripe' or 'paypal')
- `paymentMethodId` (string, optional): Payment method ID (required for Stripe)

**Response:**
- `id`: Charge ID from the provider
- `status`: Payment status
- `provider`: Payment provider used

### POST /payments/refund

Process a full refund for a charge.

**Request Body:**
- `chargeId` (string, required): Charge ID to refund (provider auto-detected from ID format)

**Response:**
- `id`: Refund ID
- `status`: Refund status
- `provider`: Payment provider used

### GET /payments/history

Get payment history for the authenticated user. Returns paginated results using cursor-based pagination, aggregating from all providers.

**Query Parameters:**
- `cursor` (string, optional): Pagination cursor
- `limit` (number, optional): Items per page (default: 20)

## Configuration

The service requires the following environment variables:

- `STRIPE_SECRET_KEY`: Stripe API secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret
- `PAYPAL_CLIENT_ID`: PayPal API client ID
- `PAYPAL_SECRET`: PayPal API secret key

## Non-Functional Requirements

- Rate limit: 100 requests per 15 minutes per IP
- Response time: < 2s for charge operations
- Availability: 99.9% uptime SLA
