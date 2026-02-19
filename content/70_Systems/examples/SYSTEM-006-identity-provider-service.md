---
id: SYSTEM-006
type: system
title: Identity Provider Service
status: approved
owner: User Engineering
owner_team: User Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-10-02T13:50:57.715Z'
updated: '2026-10-05T22:50:47.947Z'
tags:
  - system
  - user-authentication
summary: Identity Provider Service
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/identity-provider-service
dependencies:
  - User Directory Service
  - MFA Gateway Service
runbooks:
  - RUNBOOK-010
  - RUNBOOK-008
example: true
---

## Overview

The Identity Provider Service (IdP) is the central authentication authority for all user-facing products and internal services. It handles user authentication, issues JWT access tokens and refresh tokens, manages sessions, and federates identity with external SSO providers (Okta, Azure AD, Google Workspace). All user logins, token issuance, MFA challenges, and OAuth authorization flows pass through this service.

The service processes approximately 25,000 authentication events per day with peak activity of 800 logins per minute during business hours. It is the single most critical service in the platform: any degradation directly blocks user access to all products.

## Architecture

The service is built on a serverless architecture using AWS Lambda for request handling, with Node.js 20 as the runtime. This provides cost-efficient scaling during off-peak hours and automatic horizontal scaling during login spikes without pre-provisioning.

The authorization server component implements OpenID Connect 1.0 and OAuth 2.0, exposing standard endpoints: `/authorize`, `/token`, `/userinfo`, `/introspect`, `/revoke`, and `/.well-known/openid-configuration`. JWT tokens are signed using RS256 with a 2048-bit RSA key pair managed in AWS Secrets Manager with a 90-day rotation schedule.

Session state is stored in Redis 7 with a 24-hour maximum TTL. The user credential store uses DynamoDB for high availability and automatic scaling. MFA challenges are delegated to the MFA Gateway Service via an internal API.

## Repositories

- [identity-provider-service](https://git.example.com/acme/identity-provider-service) - Application code, Lambda handlers, test suites, deployment configuration
- [identity-provider-infrastructure](https://git.example.com/acme/identity-provider-infrastructure) - Terraform modules for Lambda, DynamoDB, Redis, API Gateway, and IAM roles

## Runtime Environment

The service runs as a set of AWS Lambda functions behind an API Gateway, deployed across 3 availability zones (us-east-1). Lambda concurrency is configured with a reserved capacity of 50 concurrent executions and a maximum limit of 500 to prevent adjacent service starvation during load spikes.

DynamoDB tables use on-demand capacity mode with point-in-time recovery enabled. Redis 7 is deployed as an ElastiCache cluster with 2 nodes in multi-AZ mode, with automatic failover configured.

Secrets (JWT signing keys, OAuth client secrets, SSO provider credentials) are stored in AWS Secrets Manager with rotation policies enforced. Environment configuration is managed via AWS Systems Manager Parameter Store.

## Dependencies

- **User Directory Service**: Provides user profile data and credential verification; called on every login request
- **MFA Gateway Service**: Handles TOTP validation, SMS OTP delivery, and WebAuthn assertion verification; called for all MFA-enrolled users
- **Redis 7 (ElastiCache)**: Session store and OAuth token store; critical path dependency for session creation and validation
- **DynamoDB**: Persistent store for user records, refresh tokens, and audit logs
- **AWS Secrets Manager**: Stores and rotates JWT signing keys and provider credentials
- **External SSO Providers**: Okta, Azure AD, Google Workspace (optional path for SSO-configured users)
