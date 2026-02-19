---
id: TDD-027
type: tdd
title: Data Quality Validation Framework TDD
status: draft
owner: Senior Engineer
created: '2025-06-10T00:28:28.757Z'
updated: '2026-12-09T05:49:48.241Z'
tags:
  - tdd
  - data-pipeline
summary: Data Quality Validation Framework TDD
related_adrs:
  - ADR-0023
  - ADR-0024
example: true
---

## Summary

Design the Data Quality Validation Framework — a Lambda-based rules engine that evaluates completeness, uniqueness, referential integrity, and freshness rules against Iceberg tables in the data lake. The framework publishes pass/fail metrics per table and rule, triggers alerting on threshold breaches, and produces a queryable quality history for trend analysis.

This TDD applies the Iceberg table format established in [[ADR-0023|ADR-0023: Use Apache Iceberg for Data Lake Format]] and the dbt transformation layer from [[ADR-0024|ADR-0024: Adopt dbt for Data Transformations]] as the primary source of validated mart tables.

## Overview

The Data Quality Validation Framework is a Python Lambda application that runs on an Airflow-triggered schedule after each dbt transformation run completes. It reads quality rule definitions from a YAML configuration store in S3, executes Trino queries against Iceberg tables to evaluate each rule, writes results to a DynamoDB quality history table, publishes CloudWatch custom metrics per rule, and triggers SNS alerts on threshold breaches.

Key design principles:
- **Configuration-as-code**: All quality rules defined in YAML under version control; no database UI required to add or modify rules
- **Stateless execution**: Each Lambda invocation is fully independent; history is in DynamoDB, not Lambda state
- **Pluggable rule types**: Rule type handlers are independently registered; adding a new rule type requires only a new handler class
- **Threshold-based alerting**: Each rule has a configurable pass threshold; breaches publish to SNS topics consumed by PagerDuty

## Architecture

### Component Diagram

The framework has three layers:

- **Rule Loader**: Reads YAML rule definitions from S3; validates rule schema; instantiates typed rule handlers
- **Rule Executor**: Invokes the appropriate handler for each rule type; each handler generates a Trino SQL query, executes it, and evaluates the result against the rule's threshold
- **Result Publisher**: Writes pass/fail results to DynamoDB; emits CloudWatch metrics; triggers SNS on threshold breach

### Rule Types

- **`completeness`**: % of non-null values in a column — `COUNT(*) - COUNT(col) / COUNT(*)`
- **`uniqueness`**: % of unique values in a column — `COUNT(DISTINCT col) / COUNT(*)`
- **`referential_integrity`**: % of values with matching FK — `COUNT(matched) / COUNT(source)`
- **`freshness`**: Hours since most recent record — `DATE_DIFF('hour', MAX(event_time), NOW())`
- **`row_count`**: Absolute row count within range — `COUNT(*)` vs. min/max bounds

## Information Model

### Core Entities

- **QualityRule**: Rule definition from YAML. Fields: `rule_id`, `table`, `column`, `rule_type`, `threshold`, `severity`, `description`, `enabled`
- **QualityResult**: Execution result. Fields: `rule_id`, `table`, `evaluated_at`, `pass`, `observed_value`, `threshold`, `query_duration_ms`
- **QualityAlert**: Published to SNS on breach. Fields: `rule_id`, `table`, `severity`, `observed_value`, `threshold`, `breach_time`

### DynamoDB Schema

- `quality_results` table: partition key `rule_id`, sort key `evaluated_at`; GSI on `(table, evaluated_at)` for per-table history queries
- TTL: 90 days on all result records

## Interfaces

### Rule Handler Interface

```python
class RuleHandler(ABC):
    @abstractmethod
    def build_query(self, rule: QualityRule) -> str:
        """Return Trino SQL that returns a single numeric value."""

    @abstractmethod
    def evaluate(self, rule: QualityRule, observed: float) -> bool:
        """Return True if the observed value passes the rule threshold."""
```

### Rule Configuration YAML Format

```yaml
rules:
  - rule_id: orders_completeness_customer_id
    table: data_lake_prod.marts.orders
    column: customer_id
    rule_type: completeness
    threshold: 0.999
    severity: P1
    enabled: true
```

## Files and Layout

```
src/
  handler.py                    - Lambda entry point
  rule_loader.py                - YAML rule loading from S3
  executor.py                   - Rule execution orchestrator
  rules/
    completeness.py             - Completeness rule handler
    uniqueness.py               - Uniqueness rule handler
    referential_integrity.py    - Referential integrity handler
    freshness.py                - Freshness rule handler
    row_count.py                - Row count rule handler
  result_publisher.py           - DynamoDB + CloudWatch + SNS publisher
  trino_client.py               - Trino connection wrapper
  models.py                     - QualityRule, QualityResult, QualityAlert
rules/
  staging/                      - YAML rule files for staging layer tables
  marts/                        - YAML rule files for mart layer tables
```

## Work Plan

1. **Phase 1 — Rule Engine Core (Week 1-2)**: YAML loader, rule handler interface, completeness and uniqueness handlers, Trino client
2. **Phase 2 — Result Publishing (Week 3)**: DynamoDB writer, CloudWatch metric emitter, SNS alert publisher
3. **Phase 3 — Additional Rule Types (Week 4)**: Referential integrity, freshness, row count handlers
4. **Phase 4 — Airflow Integration (Week 5)**: Lambda trigger DAG, rule set configuration for all mart tables, baseline threshold calibration
5. **Phase 5 — Quality Dashboard (Week 6)**: CloudWatch dashboard for per-table pass rate, breach history, trend visualization

## Risks and Mitigations

- **Risk**: Trino query cost for large tables causes Lambda timeout. **Mitigation**: Rule queries use approximate aggregates (HyperLogLog for uniqueness) and partition-pruned scans; Lambda timeout set to 15 minutes with per-rule timeout of 60 seconds.
- **Risk**: YAML rule misconfiguration causes false positives. **Mitigation**: Rule schema validated at load time using pydantic; validation errors block Lambda execution and trigger a configuration alert.
- **Risk**: DynamoDB write throttling on large rule sets. **Mitigation**: Results are batched via `batch_write_item`; write capacity auto-scaling is enabled on the quality_results table.
- **Risk**: Alert fatigue from noisy rules. **Mitigation**: P2/P3 rules publish to a digest SNS topic (daily rollup); only P1 rules trigger immediate PagerDuty pages.

## Operations

- **Deployment**: Lambda deployed via Terraform; rule YAML files deployed from the data-pipeline repository CI pipeline.
- **Monitoring**: CloudWatch dashboard showing per-table rule pass rate, breach count, evaluation latency.
- **Alerting**: P1 rule breach triggers PagerDuty page; P2/P3 breaches aggregate to daily digest email.
- **Rollback**: Lambda version aliases allow instant rollback to previous deployment; YAML rule files versioned in S3 with point-in-time restore enabled.
