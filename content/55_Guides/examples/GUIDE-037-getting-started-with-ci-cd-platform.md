---
id: GUIDE-037
type: guide
title: Getting Started with CI/CD Platform
status: approved
owner: Developer Experience
created: '2024-11-11T16:47:07.302Z'
updated: '2025-05-10T01:58:29.377Z'
tags:
  - guide
  - ci-cd-platform
summary: Getting Started with CI/CD Platform
audience: internal
related_systems:
  - SYSTEM-032
example: true
---

## Why This Matters

The CI/CD platform is the delivery backbone for every service in the engineering organization. Every code change you merge will travel through this platform — being built, tested, scanned, and deployed — before it reaches customers. Understanding how it works helps you move faster, debug failures independently, and build with confidence knowing that automated gates protect production.

This guide covers the essentials for engineers who are new to the platform or onboarding a new service.

## Prerequisites

Before following this guide, ensure you have the following in place:

- Your GitHub (or GitLab) account has been added to the engineering organization
- You have access to the container registry namespace for your team
- Your service has a canonical name registered in the service catalog
- You have read access to the platform team's template repository (`platform/ci-templates`)
- You have requested secrets manager access for your service account from the platform team

## Setting Up Your First Pipeline

Every new service starts by copying the approved pipeline template for your language/framework. The template lives in `platform/ci-templates` and includes all required stages: lint, test, build, security-scan, and publish.

1. Clone the template for your language: `cp platform/ci-templates/node-service/.github/workflows/ci.yml .github/workflows/ci.yml`
2. Edit the `env:` block at the top of the workflow file to set your service name and registry namespace
3. Open a pull request — the CI pipeline will run automatically on every push
4. Review the pipeline output in the "Actions" tab of your repository
5. Once the pipeline passes, request platform team sign-off on your onboarding checklist

The first pipeline run will take longer than subsequent runs because the cache has not been populated yet. Normal build times for most services are under 5 minutes after the first run.

## Understanding Pipeline Stages

The platform pipeline enforces a fixed stage order. Each stage must pass before the next begins:

- **Lint**: Runs your language's linter and style checker. Failures here mean code style violations or syntax errors.
- **Test**: Runs the full unit and integration test suite. Code coverage must meet the minimum threshold (80%) or the pipeline fails.
- **Build**: Compiles the application and produces a Docker image tagged with the commit SHA.
- **Security scan**: Runs Trivy against the built image to check for CVEs. Critical and high CVEs block the pipeline unless an exception is approved.
- **Publish**: Pushes the signed image to the container registry. This stage only runs on the main branch or tagged commits.

## Next Steps

Once your pipeline is running successfully, the following resources will help you go deeper:

- Read the Writing Effective CI Pipeline Configurations guide to learn how to tune caching, parallelism, and timeout settings
- Set up branch protection rules in your repository to require CI passing before pull requests can be merged
- Contact the platform team to configure deployment notifications and register your service in the deployment approval system
- Review the Container Image Security Scanning Guide to understand how to interpret and action security scan results
