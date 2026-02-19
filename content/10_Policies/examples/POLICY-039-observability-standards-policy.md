---
id: POLICY-039
type: policy
title: Observability Standards Policy
status: approved
owner: CISO
created: '2024-07-18T10:10:15.992Z'
updated: '2025-06-05T06:12:21.630Z'
tags:
  - policy
  - monitoring-stack
summary: Observability Standards Policy
example: true
related_standards:
  - STANDARD-044
  - STANDARD-043
---

## Scope

This policy establishes the minimum observability requirements for all production services. It applies to every service deployed to production, regardless of team or technology stack. All engineers writing production services, and platform teams maintaining the monitoring infrastructure, are subject to this policy.

Observability is defined as the ability to understand system behavior through metrics, logs, and traces. All three signal types are required for production readiness.

## Rationale

- Services without adequate observability cannot be reliably operated, debugged, or improved
- Inconsistent logging formats across services prevent effective log aggregation and search
- Missing traces make distributed system debugging extremely time-consuming and error-prone
- Uniform observability practices reduce mean time to resolution (MTTR) during incidents
- Observability requirements support audit, security monitoring, and compliance obligations

## Policy Statements

- All production services must expose a Prometheus-compatible `/metrics` endpoint following [[STANDARD-043|Metric Naming Convention Standard]]
- All production services must emit structured JSON logs conforming to [[STANDARD-044|Structured Logging Standard]]
- All production services must instrument at minimum the four golden signals: latency, traffic, errors, and saturation
- Distributed tracing instrumentation is required for all services that make outbound HTTP or RPC calls
- Observability configuration must be included in the service's production readiness checklist
- Metrics, logs, and traces must not contain PII or secrets; engineering teams are responsible for data sanitization
- The monitoring platform team must review observability implementations as part of new service onboarding

## Related Standards

- [[STANDARD-044|Structured Logging Standard]]
- [[STANDARD-043|Metric Naming Convention Standard]]
