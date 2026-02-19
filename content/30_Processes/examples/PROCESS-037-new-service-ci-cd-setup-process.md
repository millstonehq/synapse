---
id: PROCESS-037
type: process
title: New Service CI/CD Setup Process
status: approved
owner: Platform Lead
created: '2024-07-13T03:56:55.980Z'
updated: '2025-07-06T19:05:57.404Z'
tags:
  - process
  - ci-cd-platform
summary: New Service CI/CD Setup Process
related_standards:
  - STANDARD-042
  - STANDARD-040
related_sops:
  - SOP-070
  - SOP-066
related_systems:
  - SYSTEM-034
example: true
---

## Purpose

This process ensures that every new service launched by the engineering organization is equipped with a complete, standards-compliant CI/CD pipeline from its first commit. Without a defined onboarding process, teams often begin deploying manually or with ad-hoc automation that later requires costly remediation. By following this process, new services inherit security scanning, artifact signing, status reporting, and deployment controls from day one.

## Scope

- All net-new services being added to the production service catalog
- Services migrated from legacy deployment mechanisms to the standard CI/CD platform
- Internal platform components and tooling services managed by the platform team
- Does not apply to short-lived experimental repositories or personal sandbox environments

## Roles and Responsibilities

- **Service Owner**: Initiates the onboarding request, provides service metadata, and validates that the resulting pipeline meets the team's delivery requirements
- **Platform Engineer**: Provisions the pipeline template, configures secrets, sets up registry credentials, and hands off to the service owner
- **Security Engineer**: Reviews pipeline configuration for compliance with security standards before the first production deployment is permitted
- **Release Manager**: Registers the new service in the deployment approval system and confirms notification routing

## Triggers

- A new service repository is created and marked as production-bound in the service catalog
- A service migration ticket is raised to move an existing service to the standard platform
- Platform team initiates a bulk onboarding drive for legacy services

## Inputs

- Completed new service intake form specifying: service name, owning team, runtime language/framework, external dependencies, and target environments
- Approved service catalog entry with canonical service name
- Access credentials for target container registry and secrets manager

## Outputs

- Fully configured CI pipeline passing lint, test, build, security scan, and publish stages
- Container registry namespace created with appropriate access controls
- Pipeline status notifications routing to the correct Slack channel
- Service registered in the deployment approval and monitoring systems
- Onboarding checklist signed off by Platform Engineer and Security Engineer

## Steps

1. Service Owner submits the new service intake form and creates the service catalog entry with the canonical service name
2. Platform Engineer clones the approved pipeline template repository and customizes it for the service's language and framework
3. Platform Engineer provisions secrets in the secrets manager (registry credentials, signing keys) and configures job-scoped secret access
4. Platform Engineer creates the container registry namespace and applies the standard image retention and access control policies
5. Service Owner opens the first pull request; Platform Engineer verifies the CI pipeline runs all required stages and passes
6. Security Engineer reviews the pipeline configuration against [[STANDARD-042|Pipeline Status Reporting Standard]] and [[STANDARD-040|Build Artifact Naming Standard]]; raises findings as blocking issues
7. Platform Engineer addresses any security findings and obtains Security Engineer sign-off
8. Release Manager registers the service in the deployment approval system and configures notification routing
9. Platform Engineer marks the onboarding checklist as complete and hands off documentation to the service owner

## Controls

- No service may deploy to production until the onboarding checklist is signed off by both Platform Engineer and Security Engineer
- Pipeline template changes require review from the platform team lead before being applied to existing or new services
- All secrets provisioned during onboarding must be recorded in the secrets inventory with the owning service and rotation schedule
- Onboarding records are retained for the lifetime of the service plus 12 months
