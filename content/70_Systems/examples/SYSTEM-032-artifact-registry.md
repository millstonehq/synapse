---
id: SYSTEM-032
type: system
title: Artifact Registry
status: accepted
owner: CI/CD Engineering
owner_team: CI/CD Engineering
runtime: Lambda / Node.js 20 / DynamoDB
created: '2024-03-31T21:26:08.827Z'
updated: '2026-02-09T16:54:55.760Z'
tags:
  - system
  - ci-cd-platform
summary: Artifact Registry
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/artifact-registry
dependencies:
  - CI Runner Fleet Manager
  - Deployment Controller
runbooks:
  - RUNBOOK-044
  - RUNBOOK-077
example: true
---

## Overview

The Artifact Registry is the authoritative store for all versioned build artifacts produced by the CI/CD platform. It stores container images, compiled binaries, test reports, and deployment manifests. Every artifact is indexed by repository, commit SHA, and semantic version, enabling downstream services to reliably resolve and promote artifacts through environment stages.

The registry handles approximately 2,400 artifact pushes per day and serves reads from the Deployment Controller and CI runners on demand. It is the single source of truth for artifact provenance and promotion history.

## Architecture

- **API Layer**: Lambda-based REST API for push, pull, tag, promote, and delete operations. Requests authenticated via HMAC-signed tokens issued by the CI Runner Fleet.
- **Storage Layer**: S3-backed blob storage with DynamoDB metadata index. Artifacts are keyed by `{repo}/{sha}/{type}/{name}`. Content-addressed storage prevents duplicate uploads.
- **Promotion Model**: Artifacts advance through promotion stages (ci → staging → production) via explicit API calls. Each promotion records approver identity, timestamp, and target environment.
- **Retention Policy**: CI artifacts are retained 30 days. Staging artifacts are retained 90 days. Production-promoted artifacts are retained indefinitely until explicitly archived.
- **Integrity**: SHA-256 checksums are stored alongside every artifact. The Deployment Controller verifies checksums before deployment.

## Repositories

- [artifact-registry](https://git.example.com/acme/artifact-registry) - Application code, Lambda functions, DynamoDB schema

## Runtime Environment

- **Platform**: Lambda / Node.js 20 / DynamoDB
- **Deployment**: Serverless Framework via ArgoCD-triggered Lambda deployment pipeline
- **Configuration**: AWS SSM Parameter Store for registry signing keys and retention overrides

## Dependencies

- CI Runner Fleet Manager - pushes artifacts on build completion
- Deployment Controller - pulls artifacts for environment promotion
- DynamoDB - artifact metadata and promotion history
- S3 - artifact blob storage

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Push latency | P95 < 3s for artifacts up to 500MB |
| Pull latency | P95 < 1s for metadata; P95 < 10s for large blobs |
| Recovery | MTTR < 15 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-044|Artifact Registry Availability Runbook]]
- [[RUNBOOK-077|CI Build Artifact Corruption Runbook]]
