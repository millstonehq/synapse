---
id: TDD-031
type: tdd
title: Pipeline Orchestration Engine TDD
status: approved
owner: Principal Engineer
created: '2024-12-27T08:03:25.265Z'
updated: '2026-10-20T18:01:46.318Z'
tags:
  - tdd
  - ci-cd-platform
summary: Pipeline Orchestration Engine TDD
related_adrs:
  - ADR-0026
  - ADR-0027
example: true
---

## Summary

The Pipeline Orchestration Engine is the central scheduling and execution component of the CI/CD platform. It receives pipeline trigger events, resolves the directed acyclic graph (DAG) of stages and jobs, distributes work to the appropriate runner pools, and tracks execution state through to completion or failure. The engine must handle thousands of concurrent pipeline runs without contention, support fan-out parallelism within a pipeline, and provide accurate real-time status to the API layer.

This design follows the DAG execution model adopted in [[ADR-0026|ADR-0026]] and the runner dispatch contract specified in [[ADR-0027|ADR-0027]].

## Overview

- The engine operates as a stateless coordinator: all pipeline and job state is persisted in the backing store, allowing multiple engine replicas to share load without coordination overhead.
- Pipeline definitions are resolved into an immutable execution plan at trigger time, so late changes to pipeline config do not affect in-flight runs.
- Stage readiness is evaluated on every job completion event, enabling fine-grained fan-out without a polling loop.
- The engine communicates with runner agents exclusively via a durable job queue, decoupling execution capacity from orchestration capacity.
- Concurrency limits are enforced per-project and per-runner-pool at enqueue time to prevent resource starvation across tenants.

## Architecture

- **Trigger Ingestor**: Consumes VCS webhook events and scheduled trigger messages, validates them against project configuration, and emits `pipeline.requested` domain events to the orchestration queue.
- **Execution Planner**: Resolves the pipeline YAML into an `ExecutionPlan` struct — an adjacency list of stages with per-job resource requirements, timeout values, and dependency edges.
- **Stage Scheduler**: Listens for `job.completed` and `job.failed` events; evaluates the DAG to determine which downstream stages are now unblocked; enqueues ready jobs onto the runner dispatch queue.
- **State Store**: PostgreSQL-backed repository for `PipelineRun`, `StageRun`, and `JobRun` entities; uses optimistic locking on status fields to prevent split-brain updates from concurrent replicas.
- **Timeout Watchdog**: A background goroutine that scans for jobs and stages that have exceeded their configured deadline and emits synthetic `job.timed_out` events to drive normal failure handling.

## Information Model

- **PipelineRun**: Represents one execution of a pipeline definition. Key fields: `id`, `project_id`, `pipeline_ref`, `trigger_type`, `trigger_sha`, `status`, `created_at`, `finished_at`.
- **StageRun**: One stage within a `PipelineRun`. Fields: `id`, `pipeline_run_id`, `stage_name`, `status`, `depends_on` (array of stage names), `started_at`, `finished_at`.
- **JobRun**: One job within a `StageRun`. Fields: `id`, `stage_run_id`, `job_name`, `runner_pool`, `runner_id`, `status`, `exit_code`, `log_key`, `queued_at`, `started_at`, `finished_at`.
- **ExecutionPlan**: Ephemeral struct, not persisted. Holds the resolved DAG, resource requests, and timeout configuration derived from the pipeline YAML at trigger time.
- Status values form a shared enum: `pending`, `queued`, `running`, `passed`, `failed`, `cancelled`, `timed_out`, `skipped`.

## Interfaces

- `POST /internal/v1/orchestration/trigger` — Accepts a validated trigger payload from the Trigger Ingestor and creates a `PipelineRun` with its initial `StageRun` and `JobRun` records.
- `POST /internal/v1/orchestration/job-event` — Receives job lifecycle events (`started`, `completed`, `failed`) from runner agents via the job queue consumer and advances DAG state.
- `GET /v1/pipelines/{run_id}/status` — Returns the current status tree for a pipeline run, including per-stage and per-job status, for display in the UI and API.
- `POST /v1/pipelines/{run_id}/cancel` — Marks a run and all pending/queued jobs as `cancelled`; sends cancellation messages to runners holding active jobs.
- `GET /v1/pipelines/{run_id}/jobs/{job_id}/log-url` — Returns a presigned URL to the job log stored in object storage, resolved from `JobRun.log_key`.

## Files and Layout

The orchestration engine is implemented as a dedicated service within the CI/CD platform monorepo. It shares the `internal/domain` package with other platform services for common entity types and event definitions, but owns its own use-case and repository packages.

```
services/orchestration/
  cmd/server/main.go            # Entry point, dependency wiring
  internal/
    handler/                    # HTTP handlers for trigger and job-event endpoints
    usecase/
      plan.go                   # ExecutionPlan resolution from pipeline YAML
      schedule.go               # DAG readiness evaluation and job enqueue logic
      cancel.go                 # Cancellation propagation
    repository/
      pipeline_run.go           # PipelineRun persistence
      stage_run.go              # StageRun persistence
      job_run.go                # JobRun persistence
    watchdog/
      timeout.go                # Deadline scanner and synthetic event emitter
    queue/
      producer.go               # Job dispatch to runner queue
      consumer.go               # Job event consumption from runner queue
  migrations/                   # SQL schema migrations
  deploy/
    helm/                       # Kubernetes Helm chart for the orchestration service
```

## Work Plan

1. **Phase 1 - Data model and schema (Week 1)**: Define `PipelineRun`, `StageRun`, and `JobRun` structs, write PostgreSQL migrations, implement repository layer with optimistic locking.
2. **Phase 2 - Execution planner (Week 2)**: Implement YAML-to-`ExecutionPlan` resolution, DAG validation (cycle detection, undefined dependency references), and unit test coverage.
3. **Phase 3 - Stage scheduler (Week 3-4)**: Implement DAG readiness evaluation on job completion events, job enqueue logic with concurrency limit enforcement, and end-to-end integration tests using a local queue stub.
4. **Phase 4 - Runner queue integration (Week 5)**: Wire the real job dispatch queue (Kafka topic), implement the job event consumer, and run load tests against a staging runner pool.
5. **Phase 5 - Watchdog and cancellation (Week 6)**: Implement the timeout watchdog, cancellation propagation, and the `cancel` API endpoint; verify behaviour under partial failures.
6. **Phase 6 - Observability and hardening (Week 7)**: Add Prometheus metrics for queue depth, DAG evaluation latency, and timeout rate; structured logging for all state transitions; production readiness review.

## Risks and Mitigations

- **DAG evaluation hot path becomes a bottleneck under high job completion rates**: Batch job completion events within a short window (50ms) before evaluating readiness, reducing evaluation frequency without increasing latency meaningfully.
- **Optimistic lock contention on `PipelineRun` status updates across replicas**: Partition pipeline runs to a preferred replica using consistent hashing on `pipeline_run_id`; fall back to retry on contention rather than blocking.
- **Runner agents go offline mid-job, leaving runs stuck in `running` state**: The timeout watchdog covers this case; additionally, runner heartbeat absence triggers a synthetic `job.failed` event after a configurable grace period.
- **Pipeline YAML changes deployed mid-run alter the intended execution graph**: Snapshot the resolved `ExecutionPlan` into the `PipelineRun` record at trigger time so that subsequent config changes have no effect on in-flight runs.
