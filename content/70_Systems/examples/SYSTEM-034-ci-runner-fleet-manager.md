---
id: SYSTEM-034
type: system
title: CI Runner Fleet Manager
status: approved
owner: CI/CD Engineering
owner_team: CI/CD Engineering
runtime: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
created: '2024-06-05T10:48:03.102Z'
updated: '2025-03-21T13:21:08.133Z'
tags:
  - system
  - ci-cd-platform
summary: CI Runner Fleet Manager
sla: 99.99% monthly uptime
repos:
  - https://git.example.com/acme/ci-runner-fleet-manager
dependencies:
  - Artifact Registry
  - Build Orchestration Service
runbooks:
  - RUNBOOK-043
  - RUNBOOK-048
example: true
---

## Overview

The CI Runner Fleet Manager provisions, manages, and autoscales the pool of CI runner instances that execute build jobs. It maintains a register of available runners, dispatches jobs from the Build Orchestration Service queue, monitors runner health via heartbeat, and recycles or terminates unhealthy instances. The fleet spans ephemeral Kubernetes-based runners and persistent on-premise runners for jobs requiring hardware access.

The fleet sustains a steady-state pool of 60 runners scaling up to 200 during peak hours. Runner utilization is tracked in real time and drives the autoscale policy.

## Architecture

- **Registration API**: Runners self-register on startup and deregister on graceful shutdown. Registration records runner capability tags (e.g., `docker`, `gpu`, `large-memory`) used for job routing.
- **Dispatch Engine**: Polls the Build Orchestration Service job queue and assigns jobs to idle runners matching the job's capability requirements. Uses a weighted bin-packing algorithm to balance load.
- **Heartbeat Monitor**: Expects a heartbeat from each running job every 30 seconds. Jobs missing 3 consecutive heartbeats are marked stale and reclaimed.
- **Autoscaler**: Monitors queue depth and runner utilization. Scales up Kubernetes runner pods when queue depth exceeds 20 jobs per available runner. Scales down after 10 minutes of low utilization.
- **Artifact Push**: Runners push build artifacts directly to the Artifact Registry on job completion, then report completion status back to the fleet manager.

## Repositories

- [ci-runner-fleet-manager](https://git.example.com/acme/ci-runner-fleet-manager) - Application code, runner agent, autoscaler, Dockerfile

## Runtime Environment

- **Platform**: Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13
- **Replicas**: 3 controller pods, autoscaling runner pods via HPA
- **Deployment**: Rolling via ArgoCD

## Dependencies

- Artifact Registry - runners push artifacts on job completion
- Build Orchestration Service - receives job dispatch requests from queue
- PostgreSQL 16 - runner registry and job assignment state
- RabbitMQ 3.13 - job dispatch queue and heartbeat bus

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.99% monthly uptime |
| Job pickup latency | P95 < 60s from queue to runner start |
| Fleet scale-up time | < 3 minutes to add 40 runners |
| Recovery | MTTR < 15 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-043|CI Runner Fleet Runbook]]
- [[RUNBOOK-048|Build Orchestration Service Runbook]]
