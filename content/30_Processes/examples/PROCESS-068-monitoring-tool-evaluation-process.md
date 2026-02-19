---
id: PROCESS-068
type: process
title: Monitoring Tool Evaluation Process
status: approved
owner: Platform Lead
created: '2025-12-06T08:07:17.812Z'
updated: '2026-10-23T02:35:04.577Z'
tags:
  - process
  - monitoring-stack
related_standards:
  - STANDARD-044
  - STANDARD-047
related_sops:
  - SOP-079
  - SOP-071
related_systems:
  - SYSTEM-036
example: true
---

## Purpose

Ensure that any new monitoring tool, observability platform component, or alerting integration adopted by the organization is evaluated consistently, with documented rationale and proof-of-concept results, before it is integrated into the production monitoring stack. This process prevents ad-hoc tool adoption that creates fragmentation, increases operational burden, or introduces unvalidated dependencies into the platform that other teams rely on.

## Scope

This process applies to:

- New monitoring, observability, or alerting tools proposed for production use
- Major version upgrades to existing monitoring stack components when the upgrade introduces breaking changes or new configuration models
- Third-party SaaS monitoring integrations
- Open-source tools proposed as replacements for existing components

**Out of scope:** Minor version upgrades and patch releases to existing tools, configuration changes to existing tools, and internal tooling that does not integrate with the production monitoring stack.

## Roles and Responsibilities

- **Proposer** - The engineer or team proposing the new tool. Responsible for completing the evaluation form, executing the POC, documenting results, and presenting findings to the review panel.
- **Platform Lead** - Process owner. Responsible for convening the review panel, ensuring evaluation criteria are met, and making the adoption or rejection decision.
- **Review Panel** - Platform Lead, one senior engineer from the monitoring team, and one representative from the primary user team (typically a service team tech lead). Responsible for reviewing POC results and making the adoption decision.
- **On-Call Rotation Owner** - The engineer responsible for the monitoring-stack on-call rotation. Must sign off on any tool that affects alerting or incident detection, as it changes on-call operational responsibilities.
- **Security Review** - Required for tools that handle log data, metric data containing PII, or that require network access outside the cluster. Security review is performed by the Security Team, not the Review Panel.

## Triggers

- An engineer or team identifies a gap in monitoring capability that an existing tool does not address
- A vendor or community evaluation reveals that an existing tool is end-of-life or significantly outperformed by an alternative
- An ADR is raised proposing a change to the monitoring stack's core components
- The quarterly tool evaluation review identifies a component for replacement

## Inputs

- Evaluation request form: tool name, version, proposed use case, which existing tool (if any) it replaces or supplements, proposing team
- Access to a staging or evaluation cluster for POC execution
- Baseline metrics from the current tool being evaluated against (for replacement evaluations)
- Completed [[STANDARD-044|Alert Quality Standard]] checklist if the tool involves alert rule evaluation or routing
- For tools that will define or track SLOs: completed [[STANDARD-047|SLO Definition Standard]] compatibility checklist

## Outputs

- Evaluation report: POC results, performance benchmarks, operational complexity assessment, cost estimate, security review outcome
- Adoption decision: adopt, adopt with conditions, defer, or reject — documented in an ADR
- If adopted: integration plan with timeline, responsible engineer, and rollout approach
- If rejected: rejection rationale documented for future reference to prevent duplicate evaluations

## Steps

1. **Proposer** submits the evaluation request form to the Platform Lead. The form must include: tool name and version, proposed use case (what problem it solves), the existing tool it supplements or replaces, estimated engineering effort for POC, and a brief description of why existing tools are insufficient.

2. **Platform Lead** reviews the request within 5 business days. If the request is clearly out of scope or duplicates an existing tool's functionality, the Platform Lead rejects it at intake with written rationale. If accepted, the Platform Lead assigns a POC environment and schedules a review panel session.

3. **Proposer** executes the POC in the evaluation environment using the standard evaluation criteria (see below). The POC duration is a minimum of 2 weeks for infrastructure-level tools and 1 week for integration-level tools. The Proposer documents results against each evaluation criterion.

4. **Security Review** (if required) is conducted in parallel with step 3. The Security Team reviews data handling, network requirements, and credential management. The security review must be complete before the Review Panel session.

5. **On-Call Rotation Owner** reviews the POC results specifically for operational impact: Does this tool change alert routing? Does it require new runbook procedures? Does it add complexity to incident diagnosis? The On-Call Rotation Owner provides a written assessment.

6. **Review Panel** convenes to review the evaluation report, security review outcome, and on-call assessment. The panel makes one of four decisions:
   - **Adopt**: Tool is approved for production integration. Proposer proceeds to integration planning.
   - **Adopt with conditions**: Tool is approved subject to specific changes (configuration, security controls, or operational procedures) being completed before production deployment.
   - **Defer**: POC was inconclusive; a longer evaluation or additional criteria are needed before a decision can be made.
   - **Reject**: Tool does not meet requirements or introduces unacceptable risk. Rejection is documented with rationale.

7. **If adopted**, the Proposer drafts an ADR documenting the decision, the alternatives considered, and the rationale. The ADR is submitted for review following the standard ADR process. Integration work begins after the ADR is approved.

8. **If the tool replaces an existing component**, the Proposer follows the [[SOP-079|Monitoring Stack Component Migration SOP]] for cutover. Decommissioning the old tool requires a separate change ticket and must be coordinated with the [[SYSTEM-036|Metrics Collection Service]] team if the old tool feeds into the collection pipeline.

9. **Post-adoption review**: 30 days after the tool reaches 100% production adoption, the Proposer presents a post-adoption review to the Platform Lead covering: actual vs. expected performance, any operational issues, and whether the evaluation criteria were accurate. Findings are used to improve future evaluations.

## Controls

- No new monitoring tool may be deployed to production without a completed evaluation report and Review Panel approval
- POC must be executed in the staging environment; production trial deployments are not permitted without explicit Review Panel approval
- Security review is mandatory for tools that handle log or trace data; it cannot be waived
- All adoption decisions are documented in ADRs retained for the life of the tool in production
- The quarterly tool evaluation review (per [[SOP-071|Quarterly Tool Review SOP]]) ensures that adopted tools continue to meet requirements and that rejected tools are not re-evaluated without new evidence
- Tools that modify alert routing or evaluation must be reviewed by the On-Call Rotation Owner; this sign-off cannot be delegated

## Evaluation Criteria

POCs are assessed against these standard criteria:

| Criterion | Description |
|-----------|-------------|
| Functional coverage | Does the tool address the stated use case? Are there capability gaps vs. the existing tool? |
| Performance | Ingestion throughput, query latency, and resource consumption under production-representative load |
| Operational complexity | Setup complexity, configuration management, upgrade path, and runbook requirements |
| Compatibility | Integration with existing monitoring stack components (Prometheus, Grafana, AlertManager, OTel Collector) |
| Reliability | Availability, data durability, and failure mode behavior |
| Security | Data handling, credential management, network exposure, audit log support |
| Cost | Licensing cost, infrastructure cost, and engineering cost of adoption and ongoing maintenance |
| Community and support | Project maturity, release cadence, vendor support (if commercial), known EOL timeline |
