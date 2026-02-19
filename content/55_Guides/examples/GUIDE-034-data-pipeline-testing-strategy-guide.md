---
id: GUIDE-034
type: guide
title: Data Pipeline Testing Strategy Guide
status: review
owner: Engineering Team
created: '2025-07-19T00:25:50.660Z'
updated: '2026-02-07T02:28:14.250Z'
tags:
  - guide
  - data-pipeline
summary: Data Pipeline Testing Strategy Guide
audience: internal
related_systems:
  - SYSTEM-028
  - SYSTEM-027
related_sops:
  - SOP-057
  - SOP-055
example: true
---

## Why Testing Pipelines Is Different

Data pipeline testing requires different approaches than service API testing. The behavior you need to verify is not request/response correctness but data correctness: does the transform produce the right records, the right schema, and the right aggregations given representative input data? Bugs in pipelines are often silent — the pipeline succeeds but produces wrong numbers — making automated quality verification essential.

## The Four Testing Layers

A complete pipeline testing strategy has four layers:

**Unit tests** validate individual transformation functions with small, controlled input data. These run in seconds and catch logic bugs before integration. Every transformation function must have unit tests covering the happy path, null inputs, and boundary values.

**Integration tests** validate a full pipeline stage end-to-end against a representative sample dataset. They verify output schema conformance, record count expectations, and partition write correctness. Integration tests should run in CI against a small (1-10k row) representative fixture.

**Contract tests** validate that a pipeline's output continues to meet the schema expectations of its consumers. For Kafka-based pipelines, this means running the schema registry compatibility check as part of CI. For datasets, this means running dbt schema tests (not_null, unique, accepted_values) against the output of each model.

**Data quality gate tests** run in production as part of the pipeline execution. These check completeness, uniqueness, and value-range thresholds on the actual output data and halt downstream propagation if thresholds are not met.

## Writing Good Fixture Data

The quality of pipeline tests depends heavily on fixture data that represents real-world edge cases:

- Include rows with null values in optional fields
- Include at least one row per partition boundary for date-range-sensitive transforms
- Include duplicate records if the transform is supposed to deduplicate
- Include schema-boundary values (max string length, zero values, negative numbers) for relevant fields

Store fixture data as small Parquet files or JSON fixtures in the test directory, not as hardcoded Python dictionaries.

## CI Pipeline Configuration

The test suite for data pipelines must run in CI on every PR:

- Unit tests and integration tests must complete within 10 minutes; parallelize if needed
- Contract tests (schema registry compatibility) must run for any PR that modifies an output schema
- Integration tests must use the same Python/Spark version as production
- Test failures must block merge; warnings are not sufficient for data correctness issues

## Common Testing Pitfalls

- **Testing only the happy path**: Nulls, empty partitions, and source data gaps are common in production; test them explicitly
- **Mocking the target storage entirely**: Integration tests that never actually write and read back data miss serialization and partition issues
- **Skipping idempotency tests**: Every pipeline must have a test that runs the pipeline twice and asserts identical output

## Next Steps

- Review the Data Transformation Testing Standard for the minimum coverage requirements
- Add the standard idempotency test template to all new pipelines at creation time
- Integrate dbt test results into the CI pipeline summary so quality gate failures are visible in PR checks

## How Our Pipeline Works

### Build and Test

When you merge a PR to `main`, CI automatically:

- Runs the full test suite (unit, integration, E2E)
- Builds a Docker image tagged with the commit SHA
- Pushes the image to our container registry
- Generates a deployment manifest

You don't need to do anything here. If CI fails, the merge is blocked.

### The Change Ticket

Before deploying, you need an approved change ticket. This isn't bureaucracy - it's how we:

- Track what changed and why (audit trail)
- Ensure someone besides you reviewed the risk
- Coordinate timing so deploys don't collide

For low-risk changes (config updates, small bug fixes), approval is lightweight - your PR reviewer can approve the ticket. For high-risk changes (database migrations, new services, breaking API changes), you need a senior engineer's sign-off.

### The Deploy Itself

We use blue-green deployments. This means:

- The new version spins up alongside the old one
- Health checks verify the new version is healthy
- Traffic gradually shifts from old to new
- If anything looks wrong, traffic shifts back instantly

The key insight: **rollback is always one click away**. You don't need to "fix forward" under pressure. If metrics degrade, roll back first, investigate second.

### Monitoring Window

After a deploy, we watch metrics for 15 minutes:

- **Error rate**: Should stay below 0.1%. Any spike above 1% triggers rollback.
- **Latency**: P95 should stay under 500ms. Sustained increase above 1s triggers rollback.
- **Business metrics**: Order completion rate, payment success rate should stay stable.

If you're unsure whether a metric looks normal, check the dashboards linked in the [[example-service-outage-runbook|Service Outage Runbook]] for baseline comparisons.

## Common Questions

### "Can I deploy on Friday afternoon?"

We have a soft freeze Friday after 3pm. You can deploy with senior engineer approval, but ask yourself: do you want to be debugging at 7pm on a Friday?

### "What if my change needs a database migration?"

Database migrations are always high-risk. They need:
- A tested rollback migration
- Off-peak deployment window
- DBA review for anything touching indexes or large tables

See the database migration section of the [[example-production-deployment-sop|Deployment SOP]] for the exact procedure.

### "How do I know if my change is high-risk?"

If any of these are true, it's high-risk:
- Database schema changes
- New external service dependencies
- Changes to authentication or authorization
- Breaking API changes (even behind feature flags)
- Infrastructure changes (new queues, new caches, scaling config)

## Next Steps

- Read the [[example-change-management-process|Change Management Process]] to understand the governance workflow
- Bookmark the [[example-production-deployment-sop|Production Deployment SOP]] for when you're ready to deploy
- Familiarize yourself with the [[example-service-outage-runbook|Service Outage Runbook]] before your first on-call rotation
