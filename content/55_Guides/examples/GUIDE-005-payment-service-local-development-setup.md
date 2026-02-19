---
id: GUIDE-005
type: guide
title: Payment Service Local Development Setup
status: draft
owner: Developer Experience
created: '2025-09-20T10:11:58.749Z'
updated: '2025-07-25T05:36:11.431Z'
tags:
  - guide
  - payment-processing
summary: Payment Service Local Development Setup
audience: internal
related_systems:
  - SYSTEM-001
  - SYSTEM-005
related_sops:
  - SOP-002
  - SOP-009
example: true
---

## Prerequisites

Before setting up the payment service locally, ensure you have the following installed:

- Docker Desktop 4.x or later (required for the local infrastructure stack)
- Java 21 JDK (the payment service is a Spring Boot application)
- Gradle 8.x (build tool; use the Gradle wrapper `./gradlew` to avoid version mismatches)
- AWS CLI configured with a developer profile that has access to the sandbox secrets
- Access to the internal NPM registry for payment.js SDK dependencies

You will also need sandbox API credentials for at least one payment gateway (Stripe sandbox keys are recommended for local development; request them from the platform team).

## Starting the Local Stack

The payment service depends on PostgreSQL, Redis, and a local message queue. A Docker Compose file in the repository root starts all dependencies:

```bash
# Start infrastructure dependencies
docker compose up -d postgres redis localstack

# Run database migrations
./gradlew flywayMigrate

# Start the payment service
./gradlew bootRun --args='--spring.profiles.active=local'
```

The service starts on port 8080 by default. The health check endpoint at `http://localhost:8080/health` should return `{"status":"UP"}` when the service is ready.

## Configuring Local Secrets

The local profile reads secrets from environment variables rather than AWS Secrets Manager. Create a `.env.local` file in the project root (this file is gitignored):

```
STRIPE_API_KEY=sk_test_your_sandbox_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_local_webhook_secret
DATABASE_URL=jdbc:postgresql://localhost:5432/payments_local
REDIS_URL=redis://localhost:6379
```

For webhook testing locally, use the Stripe CLI or the platform webhook simulator to forward events to `http://localhost:8080/webhooks/stripe`.

## Running Tests

```bash
# Run unit tests only (fast, no Docker required)
./gradlew test

# Run integration tests (requires Docker Compose stack running)
./gradlew integrationTest

# Run the full payment scenario test suite against local sandbox
./gradlew paymentScenarioTest
```

All tests must pass before submitting a pull request. The CI pipeline runs the full test suite including integration tests.

## Common Setup Issues

- **Port 5432 already in use**: Stop any local PostgreSQL instance before starting the Docker Compose stack.
- **`gradlew` permission denied**: Run `chmod +x gradlew` to make the wrapper executable on macOS/Linux.
- **Stripe webhook signature failures locally**: Ensure you are using the webhook secret from your `.env.local` and that the Stripe CLI is forwarding to the correct local port.
