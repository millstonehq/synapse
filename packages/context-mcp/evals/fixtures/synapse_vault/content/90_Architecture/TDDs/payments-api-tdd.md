---
id: payments-api-tdd
type: tdd
title: Payments API — Technical Design
status: approved
owner: Principal Engineer
created: "2025-06-15T00:00:00.000Z"
updated: "2025-06-15T00:00:00.000Z"
tags:
  - tdd
  - payments
  - stripe
  - api
summary: Technical design for the Payments API service using Stripe.
related_adrs: []
---

## Summary

This document describes the technical design of the Payments API. The service processes credit card payments through Stripe's API, handles refunds, and provides payment history for authenticated users.

## Architecture

The Payments API is a REST service built with Express.js and TypeScript. It uses the Stripe Node.js SDK for all payment processing.

### Components

- **Routes** (`src/routes/payments.ts`): Express router with three endpoints: `/charge`, `/refund`, `/history`
- **PaymentService** (`src/services/payment.ts`): Business logic layer wrapping the Stripe SDK
- **Config** (`src/config/index.ts`): Environment-based configuration for Stripe keys and database

### Data Flow

1. Client sends payment request to `/payments/charge`
2. Auth middleware validates JWT token
3. PaymentService creates a Stripe PaymentIntent
4. Stripe processes the charge and returns result
5. Response sent back to client

## API Endpoints

### POST /payments/charge

Process a payment charge via Stripe.

**Request Body:**
- `amount` (number, required): Amount in cents
- `currency` (string, required): ISO 4217 currency code
- `paymentMethodId` (string, required): Stripe payment method ID

**Response:**
- `id`: Stripe PaymentIntent ID
- `status`: Payment status

### POST /payments/refund

Process a full refund for a charge.

**Request Body:**
- `chargeId` (string, required): Stripe PaymentIntent ID to refund

**Response:**
- `id`: Refund ID
- `status`: Refund status

### GET /payments/history

Get payment history for the authenticated user. Returns paginated results using offset-based pagination.

**Query Parameters:**
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 20)

## Configuration

The service requires the following environment variables:

- `STRIPE_SECRET_KEY`: Stripe API secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret

## Non-Functional Requirements

- Rate limit: 100 requests per 15 minutes per IP
- Response time: < 2s for charge operations
- Availability: 99.9% uptime SLA
