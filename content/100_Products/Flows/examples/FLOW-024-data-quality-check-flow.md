---
id: FLOW-024
type: flow
title: Data Quality Check Flow
status: approved
owner: QA Lead
created: '2024-03-18T06:10:04.255Z'
updated: '2025-11-23T10:36:03.096Z'
tags:
  - flow
  - data-pipeline
summary: Data Quality Check Flow
feature_area: Data Pipeline
related_prds:
  - PRD-028
example: true
---

## Steps

### Step 1: Airflow Quality Check DAG Triggers Lambda

The Airflow quality check DAG fires after the dbt transformation DAG completes successfully. The `LambdaInvokeOperator` task calls the Data Quality Validation Framework Lambda with the rule set configuration path (pointing to the YAML rule files in S3 for the mart layer tables). The invocation is synchronous; the Airflow task waits for the Lambda to return.

### Step 2: Lambda Loads and Validates Rule Definitions

The Lambda reads the YAML rule files from S3 for all enabled rule sets. Each rule file is validated against the rule schema using pydantic. Rules with invalid configuration (unknown rule_type, missing threshold, invalid table reference) cause a validation error that fails the Lambda invocation and alerts the data engineering on-call via SNS (configuration alert topic, not PagerDuty). Rules that pass validation are instantiated as typed rule handler objects.

### Step 3: Rules Execute Against Iceberg Tables via Trino

For each enabled rule, the appropriate rule handler generates a Trino SQL query targeting the rule's table and column. The Lambda's Trino client executes the query (with a 60-second per-rule timeout). The returned numeric value is compared against the rule's threshold using the handler's evaluate method. Examples:
- Completeness rule: observed = `1 - COUNT(*) WHERE customer_id IS NULL / COUNT(*)` vs. threshold = 0.999
- Freshness rule: observed = `DATE_DIFF('hour', MAX(event_time), NOW())` vs. threshold = 2 (hours)
- Uniqueness rule: observed = `COUNT(DISTINCT order_id) / COUNT(*)` vs. threshold = 1.0

### Step 4: Results Written to DynamoDB and CloudWatch

For each rule evaluation, the Lambda writes a QualityResult item to the DynamoDB `quality_results` table (rule_id, table, evaluated_at, pass, observed_value, threshold, query_duration_ms). Results are batch-written using `batch_write_item` to reduce DynamoDB API calls. CloudWatch custom metrics are emitted per rule: `QualityRulePass` (1 or 0) and `QualityObservedValue` (the numeric result). Metrics are namespaced as `DataPlatform/QualityRules` with dimensions `RuleId`, `Table`, and `Severity`.

### Step 5: Breach Alerts Published to SNS

After all rules are evaluated, the Lambda checks for failing rules. P1 failures are published to the `data-quality-p1-breaches` SNS topic, which is subscribed by PagerDuty and triggers an immediate on-call page. P2/P3 failures are published to the `data-quality-digest` SNS topic, which aggregates and sends a daily email to the data engineering distribution list. The Lambda returns a summary to Airflow indicating the total rule count, pass count, and breach count per severity.

## Expected Results

- All enabled quality rules execute and their results are written to DynamoDB within 15 minutes of Lambda invocation
- P1 rule breaches generate a PagerDuty page within 5 minutes of the Lambda completing
- P2/P3 rule breaches are included in the next daily digest email
- The Data Quality Dashboard reflects the new rule results within 5 minutes of Lambda completion (via DynamoDB read)
- Lambda configuration errors (bad YAML) alert the data engineering team without creating false quality failures for consumers

## User Info

| Field | Value |
|-------|-------|
| Role | Data pipeline operator / on-call engineer |
| Permissions | Read access to DynamoDB quality_results table, CloudWatch metrics, Airflow DAG run history |
| Test rule set | `rules/marts/orders_quality_rules.yaml` (staging environment) |
| Test Iceberg table | `data-lake-staging.marts.orders_daily` |
| Environment | Staging |
