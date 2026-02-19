---
id: WIKI-028
type: wiki
title: Container Registry - Migration Notes
status: proposed
owner: CI/CD Team
created: '2024-02-23T11:09:02.498Z'
updated: '2026-09-22T15:29:03.476Z'
tags:
  - wiki
  - ci-cd-platform
summary: Container Registry - Migration Notes
source_repo: https://git.example.com/acme/container-registry
commit_sha: 59af23f0018af52692d3d474f8a22658fbb713fa
generated_at: '2026-02-24T09:14:18.644Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: gpt-4o
importance: low
example: true
---

## Overview

This wiki captures the decisions and operational notes from the migration of the CI/CD platform's container image storage from the legacy AWS ECR-based registry to Harbor (self-hosted). The migration was completed over a 6-week window in Q4 2024 with zero downtime by running the two registries in parallel and cutting over per-service via an image pull policy change.

This document is a living record of what was done, what broke, and what configuration was retained for future migrations.

## Architecture

### Before Migration

Images were pushed to per-team ECR repositories. There was no vulnerability scanning, no image signing, and no replication. Image pull credentials were stored as individual Kubernetes Secrets per namespace, creating a sprawling credential management problem.

### After Migration

Harbor runs on-premise in the platform cluster. All CI runners push to `registry.internal/acme/{service}:{sha}`. Harbor provides:
- Notary-based image signing enforced at push
- Trivy vulnerability scanning on every push with configurable severity gates
- Role-based project isolation per team
- Garbage collection of untagged images older than 30 days

## Key Components

### Migration Tool

A Go utility (`tools/registry-migrate`) was written to:
1. Pull each tagged image from ECR
2. Re-tag with the Harbor registry prefix
3. Push to Harbor
4. Verify digest equality

The tool processed 4,200 images over 18 hours during the initial bulk migration.

### Credential Consolidation

ECR per-namespace credentials were replaced with a single Harbor robot account secret deployed cluster-wide via a Kubernetes External Secret. All service accounts reference this single pull secret.

### Rollback Path

The ECR repositories were kept read-only for 60 days post-migration. Any service can be rolled back to ECR by reverting the `imagePullPolicy` and image prefix in its GitOps manifest.

## Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Harbor project isolation | Per-team | `acme/platform`, `acme/product`, etc. |
| Vulnerability scan gate | CRITICAL blocks push | HIGH generates a warning only |
| Image retention policy | 30 days for untagged | Tagged images retained indefinitely |
| Replication | None currently | DR replication planned for Q2 |

## Dependencies

- Harbor (self-hosted, on-platform cluster) — production registry
- Notary — image signing service
- Trivy — vulnerability scanner integrated with Harbor
- Kubernetes External Secrets — distributes Harbor robot account credentials
