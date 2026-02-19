---
id: GUIDE-057
type: guide
title: Billing Service Local Development Guide
status: approved
owner: Developer Experience
created: '2024-05-18T02:14:16.749Z'
updated: '2026-09-21T01:20:30.899Z'
tags:
  - guide
  - billing-engine
summary: Billing Service Local Development Guide
audience: internal
related_systems:
  - SYSTEM-050
  - SYSTEM-046
related_sops:
  - SOP-097
  - SOP-099
example: true
---

## Prerequisites

Before running the billing service locally, ensure you have:

- Docker Desktop (v4.20+) and Docker Compose installed
- JDK 21 installed (the billing service is a Java 21 application)
- Access to the internal package registry (for billing SDK dependencies)
- The billing service repository cloned: `git clone git@github.com:example/billing-service.git`

You do not need a local PostgreSQL or Kafka installation — these are provided by the Docker Compose stack.

## Starting the Local Stack

The local development environment is fully containerized. From the repository root:

```
docker compose -f docker-compose.dev.yml up -d
```

This starts PostgreSQL 15, Kafka (with a single broker), the tax calculation service stub, and the billing database schema migration runner. Wait for all containers to report healthy before starting the billing service itself.

To start the billing service:

```
./gradlew bootRun --args='--spring.profiles.active=local'
```

The `local` profile disables payment gateway integration (Stripe calls are intercepted by a local stub), uses an in-memory tax rate table with test data, and enables verbose billing calculation logging.

## Seed Data and Test Accounts

The local stack includes a seed script that creates a set of test accounts with different billing configurations:

- `TEST-ACCOUNT-001`: Monthly flat subscription, USD
- `TEST-ACCOUNT-002`: Usage-based (API calls), USD, with 10,000 free tier
- `TEST-ACCOUNT-003`: Multi-tier usage, GBP

Run the seed script after the stack is healthy:

```
./gradlew :db:seed --args='--profile=local-dev'
```

To emit test usage events for account `TEST-ACCOUNT-002`, use the billing test harness:

```
./gradlew :test-harness:emitUsage --args='--account=TEST-ACCOUNT-002 --quantity=5000 --type=api.request'
```

## Running Tests

The billing service has a comprehensive test suite. For unit tests:

```
./gradlew test
```

For integration tests (requires the Docker Compose stack to be running):

```
./gradlew integrationTest
```

Integration tests cover full billing cycle simulation, invoice generation, and tax calculation. They use the local PostgreSQL and Kafka instances and reset the database state between test classes.

## Common Issues

**Port conflicts**: The billing service listens on port 8082 locally. If you have another service on that port, override with `SERVER_PORT=8083` in your environment.

**Kafka not ready**: If the billing service fails to connect to Kafka on startup, wait 30 seconds and retry. Kafka can take longer to initialize than the health check reports.

## Next Steps

- Run the billing simulation script to test a full monthly cycle end-to-end: `./gradlew :test-harness:runBillingCycle`
- Review the Testing Billing Scenarios Guide for specific test case patterns
